#include "ascope.h"
                       
/* module information */
MODULE_AUTHOR("Uncle Yura");
MODULE_DESCRIPTION("Oscilloscope for Alterx EMC HAL");
MODULE_LICENSE("GPL");

static int comp_id;
hal_data_t *hal_data;
int listenfd = 0;
char sendBuff[1025];
pthread_t thread_id;
socket_req_t request;
pthread_mutex_t mxq;
int ch[NUM_CHANNELS];
trigger_t tr;
float data[NUM_SAMPLES];
int sample_pointer;
        
int rtapi_app_main(void) 
{
    int retval;
    comp_id = hal_init("ascope");
    if (comp_id < 0) return comp_id;

    //Get pointer to HAL shared memory data
    hal_data = (hal_data_t *) SHMPTR(0);

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
    serv_addr.sin_port = htons(PORT);
 
    if(bind(listenfd, (struct sockaddr*)&serv_addr, sizeof(serv_addr))<0)
    {
	    rtapi_print_msg(RTAPI_MSG_ERR,
    	    "ASCOPE: ERROR: socket bind failed\n");
	    hal_exit(comp_id);
	    return -1;
    }
    
    listen(listenfd, 10);

    pthread_mutex_init(&mxq,NULL);
    pthread_mutex_lock(&mxq);

    thread_arg_t arg = { &mxq, &request, &ch, &tr, data, &sample_pointer };
    
    if( pthread_create( &thread_id, NULL,  connection_handler, &arg ) < 0)
    {
	    rtapi_print_msg(RTAPI_MSG_ERR,
    	    "ASCOPE: ERROR: socket thread create failed\n");
	    hal_exit(comp_id);
	    return -1;
    }

    hal_ready(comp_id);
    return 0;
}

void connection_handler(void *arg)
{
    thread_arg_t *ta = arg;
    pthread_mutex_t *mtx = ta->mutex;
    int retval;
    struct timeval tv;
    fd_set readfds;
    fd_set fds;
    FD_ZERO(&fds);
    FD_SET(listenfd, &fds);
    while( !needQuit(mtx))
    {
        tv.tv_sec = 3;
        tv.tv_usec = 0;
        readfds = fds;
        retval=select(listenfd+1,&readfds, NULL, NULL,&tv);

        if(retval == -1) 
        {
            //Socket error
       	    rtapi_print_msg(RTAPI_MSG_ERR,"ASCOPE: ERROR: socket select error\n");
            break;
        } 
        else if(retval) 
        {
            //Data avaliable
            int connfd = accept(listenfd, (struct sockaddr*)NULL, NULL);
            setsockopt(connfd,SOL_SOCKET,SO_RCVTIMEO,&tv,sizeof(tv));
            
            //Read data
            int read_size=recv(connfd,ta->request,sizeof(socket_req_t),NULL);
            if( read_size != sizeof(socket_req_t))
            {
                rtapi_print_msg(RTAPI_MSG_ERR,
                    "ASCOPE: ERROR: wrong packet size\n",
                    read_size,sizeof(socket_req_t));
                continue;
            }
            /*
            rtapi_print_msg(RTAPI_MSG_ERR,"ASCOPE: DEBUG packet %X %X %X\n",
                ta->request->cmd,
                ta->request->type,
                ta->request->value);
                */
                
            if( ta->request->cmd==STOP );
            else if( ta->request->cmd==LIST )
            {
                if( ta->request->type == HAL_PIN )
                {
                    int next = hal_data->pin_list_ptr;  
                    hal_pin_t *source;
                    while(next != 0) 
                    {
                        source = SHMPTR(next);
                        snprintf(sendBuff, sizeof(sendBuff), "%s %d %X\n",\
                            source->name,source->type,next);
                        write(connfd, sendBuff, strlen(sendBuff));
                        next = source->next_ptr; 
                    }
                }
                else if( ta->request->type == HAL_SIG )
                {
                    int next = hal_data->sig_list_ptr; 
                    hal_sig_t *source;
                    while(next != 0) 
                    {
                        source = SHMPTR(next);
                        snprintf(sendBuff, sizeof(sendBuff), "%s %d %X\n",\
                            source->name,source->type,next);
                        write(connfd, sendBuff, strlen(sendBuff));
                        next = source->next_ptr; 
                    }
                }
                else if( ta->request->type == HAL_PARAMETER )
                {
                    int next = hal_data->param_list_ptr; 
                    hal_param_t *source;
                    while(next != 0) 
                    {
                        source = SHMPTR(next);
                        snprintf(sendBuff, sizeof(sendBuff), "%s %d %X\n",\
                            source->name,source->type,next);
                        write(connfd, sendBuff, strlen(sendBuff));
                        next = source->next_ptr; 
                    }
                }
                else
                {
                    rtapi_print_msg(RTAPI_MSG_ERR,
                        "ASCOPE: ERROR: wrong packet type\n");
                    continue;
                }   
            }
            else if( ta->request->cmd==STATE )
            {
                char *value_str;
                if( ta->request->type == HAL_PIN )
                {
                    hal_pin_t *source=SHMPTR(ta->request->value.u);
                    if (source->signal == 0) 
                        value_str = data_value(source->type, &(source->dummysig));
                    else 
                    {
                        hal_sig_t *sig;
                        sig = SHMPTR(source->signal);
                        value_str = data_value(source->type, SHMPTR(sig->data_ptr));
                    }
                    snprintf(sendBuff, sizeof(sendBuff), "%s %d %s\n",\
                        source->name,source->type,value_str);
                }
                else if( ta->request->type == HAL_SIG )
                {
                    hal_sig_t *source=SHMPTR(ta->request->value.u);
                    value_str = data_value(source->type, SHMPTR(source->data_ptr));
                    snprintf(sendBuff, sizeof(sendBuff), "%s %d %s\n",\
                        source->name,source->type,value_str);
                }
                else if( ta->request->type == HAL_PARAMETER )
                {
                    hal_param_t *source=SHMPTR(ta->request->value.u);
                    value_str = data_value(source->type, SHMPTR(source->data_ptr));
                    snprintf(sendBuff, sizeof(sendBuff), "%s %d %s\n",\
                        source->name,source->type,value_str);
                }
                else
                {
                    rtapi_print_msg(RTAPI_MSG_ERR,
                        "ASCOPE: ERROR: wrong packet type\n");
                    continue;
                }   
                write(connfd, sendBuff, strlen(sendBuff));
            }
            else if( ta->request->cmd==CHANNEL )
            {
                ta->channels[ta->request->type] = ta->request->value.u;
            }
            else if( ta->request->cmd==TRIG )
            {
                ta->trigger->cmd = SAMPLE_IDLE;
                ta->trigger->type = ta->request->type;
                ta->trigger->pin = ta->request->value.u;
            }
            else if( ta->request->cmd==RUN )
            {
                ta->trigger->cmd = SAMPLE_RUN;
            }
            else if( ta->request->cmd==CHECK )
            {
                if(ta->trigger->cmd != SAMPLE_COMPLETE)
                {
                    snprintf(sendBuff, sizeof(sendBuff), "Pass\n");
                    write(connfd, sendBuff, strlen(sendBuff));
                }
                else
                {
                    snprintf(sendBuff, sizeof(sendBuff), "Ready\n");
                    write(connfd, sendBuff, strlen(sendBuff));
                }
            }
            else if( ta->request->cmd==GET )
            {
            
                for(int i=0; i<*(ta->pointer);i++)
                {
                    snprintf(sendBuff, sizeof(sendBuff), "%f\n",ta->array[i]);
                    write(connfd, sendBuff, strlen(sendBuff));
                }
                
                *(ta->pointer) = 0;
            }
            else
            {
                //Wrong command
                rtapi_print_msg(RTAPI_MSG_ERR,"ASCOPE: ERROR: socket wrong command\n");
                continue;
            }
            close(connfd);
        }
    }
}

void rtapi_app_exit(void) 
{
    pthread_mutex_unlock(&mxq); 
    pthread_join(thread_id,NULL);
    hal_exit(comp_id);
}

static void communicate(void *arg, long period)
{

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

int needQuit(pthread_mutex_t *mtx)
{
    switch(pthread_mutex_trylock(mtx)) 
    {
        case 0: 
            //if we got the lock, unlock and return 1 (true)
            pthread_mutex_unlock(mtx);
            return 1;
        case EBUSY: 
            //return 0 (false) if the mutex was locked
            return 0;
    }
    return 1;
}