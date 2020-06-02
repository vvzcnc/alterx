#define RTAPI

#include <rtapi.h>		/* RTAPI realtime OS API */
#include <rtapi_app.h>		/* RTAPI realtime module decls */
#include <hal.h>		/* HAL public API decls */
#include <stdio.h>	
#include <rtapi_string.h>
#include <rtapi_stdint.h>
#include <rtapi_common.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <pthread.h>

#define SHMPTR(offset)  ( (void *)( hal_shmem_base + (offset) ) )
#define SHMOFF(ptr)     ( ((char *)(ptr)) - hal_shmem_base )
#define SHMCHK(ptr)  ( ((char *)(ptr)) > (hal_shmem_base) && \
                       ((char *)(ptr)) < (hal_shmem_base + HAL_SIZE) )
                       
/* module information */
MODULE_AUTHOR("Uncle Yura");
MODULE_DESCRIPTION("Oscilloscope for Alterx EMC HAL");
MODULE_LICENSE("GPL");

typedef union {
    hal_bit_t b;
    hal_s32_t s;
    hal_u32_t u;
    hal_float_t f;
} hal_data_u;

typedef struct {
    int next;			/* next element in list */
    int prev;			/* previous element in list */
} hal_list_t;

typedef struct {
    int version;		/* version code for structs, etc */
    unsigned long mutex;	/* protection for linked lists, etc. */
    hal_s32_t shmem_avail;	/* amount of shmem left free */
    constructor pending_constructor;
			/* pointer to the pending constructor function */
    char constructor_prefix[HAL_NAME_LEN+1];
			        /* prefix of name for new instance */
    char constructor_arg[HAL_NAME_LEN+1];
			        /* prefix of name for new instance */
    int shmem_bot;		/* bottom of free shmem (first free byte) */
    int shmem_top;		/* top of free shmem (1 past last free) */
    int comp_list_ptr;		/* root of linked list of components */
    int pin_list_ptr;		/* root of linked list of pins */
    int sig_list_ptr;		/* root of linked list of signals */
    int param_list_ptr;		/* root of linked list of parameters */
    int funct_list_ptr;		/* root of linked list of functions */
    int thread_list_ptr;	/* root of linked list of threads */
    long base_period;		/* timer period for realtime tasks */
    int threads_running;	/* non-zero if threads are started */
    int oldname_free_ptr;	/* list of free oldname structs */
    int comp_free_ptr;		/* list of free component structs */
    int pin_free_ptr;		/* list of free pin structs */
    int sig_free_ptr;		/* list of free signal structs */
    int param_free_ptr;		/* list of free parameter structs */
    int funct_free_ptr;		/* list of free function structs */
    hal_list_t funct_entry_free;	/* list of free funct entry structs */
    int thread_free_ptr;	/* list of free thread structs */
    int exact_base_period;      /* if set, pretend that rtapi satisfied our
				   period request exactly */
    unsigned char lock;         /* hal locking, can be one of the HAL_LOCK_* types */
} hal_data_t;

typedef struct {
    int next_ptr;		/* next pin in linked list */
    int data_ptr_addr;		/* address of pin data pointer */
    int owner_ptr;		/* component that owns this pin */
    int signal;			/* signal to which pin is linked */
    hal_data_u dummysig;	/* if unlinked, data_ptr points here */
    int oldname;		/* old name if aliased, else zero */
    hal_type_t type;		/* data type */
    hal_pin_dir_t dir;		/* pin direction */
    char name[HAL_NAME_LEN + 1];	/* pin name */
} hal_pin_t;

typedef struct {
    int next_ptr;		/* next signal in linked list */
    int data_ptr;		/* offset of signal value */
    hal_type_t type;		/* data type */
    int readers;		/* number of input pins linked */
    int writers;		/* number of output pins linked */
    int bidirs;			/* number of I/O pins linked */
    char name[HAL_NAME_LEN + 1];	/* signal name */
} hal_sig_t;

typedef struct {
    int next_ptr;		/* next parameter in linked list */
    int data_ptr;		/* offset of parameter value */
    int owner_ptr;		/* component that owns this signal */
    int oldname;		/* old name if aliased, else zero */
    hal_type_t type;		/* data type */
    hal_param_dir_t dir;	/* data direction */
    char name[HAL_NAME_LEN + 1];	/* parameter name */
} hal_param_t;


extern char *hal_shmem_base;
extern hal_data_t *hal_data;

static char *data_value(int type, void *valptr);
static void communicate(void *arg, long period);
static void sample(void *arg, long period);
void connection_handler(void);
static int comp_id;

hal_data_t *hal_data;

int listenfd = 0, connfd = 0;
char sendBuff[1025];
time_t ticks;

int rtapi_app_main(void) 
{
    int retval;
    comp_id = hal_init("ascope");
    if (comp_id < 0) return comp_id;

    retval = hal_export_funct("ascope.sample", sample, NULL, 0, 0, comp_id);
    if (retval != 0) 
    {
	    rtapi_print_msg(RTAPI_MSG_ERR,
    	    "ASCOPE: ERROR: sample funct export failed\n");
	    hal_exit(comp_id);
	    return -1;
    }
    
    retval = hal_export_funct("ascope.communicate", communicate, NULL, 0, 0, comp_id);
    if (retval != 0) 
    {
	    rtapi_print_msg(RTAPI_MSG_ERR,
    	    "ASCOPE: ERROR: communicate funct export failed\n");
	    hal_exit(comp_id);
	    return -1;
    }
    
    hal_data = (hal_data_t *) SHMPTR(0);
 
    listenfd = socket(AF_INET,SOCK_STREAM,0);
    if (listenfd < 0)
    {
	    rtapi_print_msg(RTAPI_MSG_ERR,
    	    "ASCOPE: ERROR: socket create failed\n");
	    hal_exit(comp_id);
	    return -1;
    }
    
    struct sockaddr_in serv_addr;

    memset(&serv_addr, '0', sizeof(serv_addr));
    memset(sendBuff, '0', sizeof(sendBuff));

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = htonl(INADDR_ANY);
    serv_addr.sin_port = htons(5000);
 
    if(bind(listenfd, (struct sockaddr*)&serv_addr, sizeof(serv_addr))<0)
    {
	    rtapi_print_msg(RTAPI_MSG_ERR,
    	    "ASCOPE: ERROR: socket bind failed\n");
	    hal_exit(comp_id);
	    return -1;
    }
    
    listen(listenfd, 10);
 
    pthread_t thread_id;
    if( pthread_create( &thread_id , NULL ,  connection_handler , NULL ) < 0)
    {
	    rtapi_print_msg(RTAPI_MSG_ERR,
    	    "ASCOPE: ERROR: socket thread create failed\n");
	    hal_exit(comp_id);
	    return -1;
    }

    hal_ready(comp_id);
    return 0;
}

void connection_handler(void)
{
    while(true)
    {
        connfd = accept(listenfd, (struct sockaddr*)NULL, NULL);

        int next;
        hal_pin_t *pin;
        hal_sig_t *sig;
        hal_param_t *param;
        char *name, *value_str;

        next = hal_data->pin_list_ptr;    
        while(next != 0) 
        {
	        pin = SHMPTR(next);
	
	        if (pin->signal == 0) 
	        {
	            value_str = data_value(pin->type, &(pin->dummysig));
	        } 
	        else 
	        {
                sig = SHMPTR(pin->signal);
	            value_str = data_value(pin->type, SHMPTR(sig->data_ptr));
            }
	
	        name = pin->name;
            snprintf(sendBuff, sizeof(sendBuff), "%s=%s\r\n", name,value_str);
            write(connfd, sendBuff, strlen(sendBuff));
            next = pin->next_ptr; 
        }
        
        close(connfd);
    }
}

void rtapi_app_exit(void) 
{
    hal_exit(comp_id);
}

static void communicate(void *arg, long period)
{
   // connfd = accept(listenfd, (struct sockaddr*)NULL, NULL);
   /*                                                                                                                                                                       
    ticks = time(NULL);
    snprintf(sendBuff, sizeof(sendBuff), "%.24s\r\n", ctime(&ticks));
    write(connfd, sendBuff, strlen(sendBuff));

    close(connfd);*/
}

static void sample(void *arg, long period)
{

}

static char *data_value(int type, void *valptr)
{
    char *value_str;
    static char buf[25];

    switch (type) 
    {
        case HAL_BIT:
        	if (*((char *) valptr) == 0)
	            value_str = "FALSE";
        	else
	            value_str = "TRUE";
    	break;
    
        case HAL_FLOAT:
	        snprintf(buf, 14, "%.7g", (double)*((hal_float_t *) valptr));
	        value_str = buf;
	    break;
        
        case HAL_S32:
	        snprintf(buf, 24, "%10ld", (long)*((hal_s32_t *) valptr));
	        value_str = buf;
	    break;
        
        case HAL_U32:
	        snprintf(buf, 24, "%10lu (0x%08lX)", (unsigned long)*((hal_u32_t *) valptr),
	            *((unsigned long *) valptr));
	        value_str = buf;
	    break;
        
        default:
	        /* Shouldn't get here, but just in case... */
	    value_str = "";
    }
    return value_str;
}