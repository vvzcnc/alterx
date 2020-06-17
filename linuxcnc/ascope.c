/*
# -*- coding: utf-8 -*-
#
# AlterX GUI - ascope - linuxcnc rt component for oscilloscope
#
# Copyright 2020-2020 uncle-yura uncle-yura@tuta.io
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
*/

#include "ascope.h"
   
/* module information */
MODULE_AUTHOR("uncle-yura (uncle-yura@tuta.io)");
MODULE_DESCRIPTION("Oscilloscope for Alterx GUI");
MODULE_LICENSE("GPL");

static int port=27267,channels=4,samples=-1;
static long int thread=1000000;
static int comp_id, shm_id;

int listenfd;

pthread_t thread_id;
hal_data_t *hal_data;
thread_arg_t *args;
channels_t *channel;
data_t *data;

RTAPI_MP_INT(port, "socket port");
RTAPI_MP_INT(channels, "number of channels");
RTAPI_MP_INT(samples, "number of samples");
RTAPI_MP_INT(thread, "sample thread");

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
    
    listenfd = socket(AF_INET,SOCK_STREAM,0);
    if (listenfd < 0)
    {
	    rtapi_print_msg(RTAPI_MSG_ERR,
    	    "ASCOPE: ERROR: socket create failed\n");
	    hal_exit(comp_id);
	    return -1;
    }

    int yes=1;
    //char yes='1';
    setsockopt(listenfd,SOL_SOCKET,SO_REUSEADDR,&yes,sizeof(yes));

    struct sockaddr_in serv_addr;
    memset(&serv_addr, 0, sizeof(serv_addr));

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = htonl(INADDR_ANY);
    serv_addr.sin_port = htons(port);
 
    if(bind(listenfd, (struct sockaddr*)&serv_addr, sizeof(serv_addr))<0)
    {
	    rtapi_print_msg(RTAPI_MSG_ERR,
    	    "ASCOPE: ERROR: socket bind failed\n");
	    hal_exit(comp_id);
	    return -1;
    }
    
    listen(listenfd, 10);

    if( samples == -1 )samples = 1000000000/thread;

    void *rptr;

    thread_arg_size_t size;
    size.channels = channels;
    size.samples = samples;

    int struct_size = sizeof(thread_arg_t) + 
                        sizeof(channels_t)*size.channels + 
                        sizeof(data_t)*size.samples;
                                        
    shm_id = rtapi_shmem_new(SHMEM_KEY,comp_id,struct_size);
        
    if (shm_id < 0) return shm_id;
    
    retval = rtapi_shmem_getptr(shm_id,&rptr);
    if (retval < 0) return retval;
    
    args = rptr;

    memset(args, 0, struct_size );

    channel = rptr + sizeof(thread_arg_t);
    data = channel + sizeof(channels_t) * size.channels;

    pthread_mutex_init(&args->mutex, NULL);
    pthread_mutex_lock(&args->mutex);
    
    if( pthread_create( &thread_id, NULL, connection_handler, &size) < 0)
    {
	    rtapi_print_msg(RTAPI_MSG_ERR,
    	    "ASCOPE: ERROR: socket thread create failed\n");
	    hal_exit(comp_id);
	    return -1;
    }

    hal_ready(comp_id);
    return 0;
}

void connection_handler(void *args)
{
    thread_arg_size_t size, *sp;
    channels_t *ch;
    data_t *array;
    thread_arg_t *ta;

    sp = args;
    
    size.channels = sp->channels;
    size.samples = sp->samples;
    
    char sendBuff[128];
    memset(sendBuff, 0, sizeof(sendBuff));

    socket_req_t *arg;
    void *rptr;
    
    int shm_id = rtapi_shmem_new(SHMEM_KEY,0,sizeof(thread_arg_t) + 
                                            sizeof(channels_t) * size.channels + 
                                            sizeof(data_t) * size.samples);
    if (shm_id < 0) return shm_id;
    
    int retval = rtapi_shmem_getptr(shm_id,&rptr);
    if (retval < 0) return retval;
    
    ta = rptr;
    ch = rptr + sizeof(thread_arg_t);
    array = ch + sizeof(channels_t) * size.channels;
        
    struct timeval tv;
    fd_set readfds;
    fd_set fds;
    FD_ZERO(&fds);
    FD_SET(listenfd, &fds);
    
    while( !need_quit(&ta->mutex))
    {
        tv.tv_sec = 1;
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
            int read_size=recv(connfd,&(ta->request),sizeof(socket_req_t),NULL);
            if( read_size != sizeof(socket_req_t))
            {
                rtapi_print_msg(RTAPI_MSG_ERR,
                    "ASCOPE: ERROR: wrong packet size %d\n",
                    read_size,sizeof(socket_req_t));
                continue;
            }
            /*
            rtapi_print_msg(RTAPI_MSG_ERR,"ASCOPE: DEBUG packet %X %X %X %X\n",
                ta->request.control,
                ta->request.cmd,
                ta->request.type,
                ta->request.value);
            */
                
            if( ta->request.cmd != OSC_LIST && 
                (int)ta->request.control.u != (int)hal_data)
            {
                rtapi_print_msg(RTAPI_MSG_ERR,
                    "ASCOPE: ERROR: wrong control word %X!=%X\n",
                    (int)ta->request.control.u, (int)hal_data);
                continue;
            }
        
            if( ta->request.cmd == OSC_STOP )
            {
                ta->trigger.cmd = SAMPLE_IDLE;
                ta->pointer = 0;
            }
            else if( ta->request.cmd == OSC_LIST )
            {
                snprintf(sendBuff, sizeof(sendBuff), "CONTROL %X\n", hal_data);
                write(connfd, sendBuff, strlen(sendBuff));
                
                if( ta->request.type == HAL_PIN )
                {
                    int next = hal_data->pin_list_ptr;  
                    hal_pin_t *source;
                    while(next != 0) 
                    {
                        source = SHMPTR(next);
                        snprintf(sendBuff, sizeof(sendBuff), "%X %d %d %s\n",\
                            next,source->type,source->dir,source->name);
                        write(connfd, sendBuff, strlen(sendBuff));
                        next = source->next_ptr; 
                    }
                }
                else if( ta->request.type == HAL_SIG )
                {
                    int next = hal_data->sig_list_ptr; 
                    hal_sig_t *source;
                    while(next != 0) 
                    {
                        source = SHMPTR(next);
                        snprintf(sendBuff, sizeof(sendBuff), "%X %d %s\n",\
                            next,source->type,source->name);
                        write(connfd, sendBuff, strlen(sendBuff));
                        next = source->next_ptr; 
                    }
                }
                else if( ta->request.type == HAL_PARAMETER )
                {
                    int next = hal_data->param_list_ptr; 
                    hal_param_t *source;
                    while(next != 0) 
                    {
                        source = SHMPTR(next);
                        snprintf(sendBuff, sizeof(sendBuff), "%X %d %d %s\n",\
                            next,source->type,source->dir,source->name);
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
            else if( ta->request.cmd == OSC_STATE )
            {
                char *value_str;
                if( ta->request.type == HAL_PIN )
                {
                    hal_pin_t *source=SHMPTR(ta->request.value.u);
                    if (source->signal == 0) 
                        value_str = get_data_value(source->type, &(source->dummysig));
                    else 
                    {
                        hal_sig_t *sig;
                        sig = SHMPTR(source->signal);
                        value_str = get_data_value(source->type, SHMPTR(sig->data_ptr));
                    }
                    snprintf(sendBuff, sizeof(sendBuff), "%s\n",value_str);
                }
                else if( ta->request.type == HAL_SIG )
                {
                    hal_sig_t *source=SHMPTR(ta->request.value.u);
                    value_str = get_data_value(source->type, SHMPTR(source->data_ptr));
                    snprintf(sendBuff, sizeof(sendBuff), "%s\n",value_str);
                }
                else if( ta->request.type == HAL_PARAMETER )
                {
                    hal_param_t *source = SHMPTR(ta->request.value.u);
                    value_str = get_data_value(source->type, SHMPTR(source->data_ptr));
                    snprintf(sendBuff, sizeof(sendBuff), "%s\n",value_str);
                }
                else
                {
                    rtapi_print_msg(RTAPI_MSG_ERR,
                        "ASCOPE: ERROR: wrong packet type\n");
                    continue;
                }   
                write(connfd, sendBuff, strlen(sendBuff));
            }
            else if( ta->request.cmd == OSC_CHANNEL )
            {
                if( ta->request.type/10 < size.channels )
                {
                    ch[ta->request.type/10].offset = ta->request.value.u;
                    ch[ta->request.type/10].type = ta->request.type%10;
                }
            }
            else if( ta->request.cmd == OSC_TRIG )
            {
                ta->trigger.cmd = SAMPLE_IDLE;
                ta->trigger.type = ta->request.type;
                ta->trigger.pin = ta->request.value.u;
            }
            else if( ta->request.cmd == OSC_RUN )
            {
                ta->pointer = 0;
                
                ta->trigger.value = ta->request.value.f;
                
                data_t l;
                if( ta->trigger.type == HAL_PIN )
                {
                    hal_pin_t *source=SHMPTR( ta->trigger.pin );
                    if (source->signal == 0) 
                        set_data_value(source->type, &(source->dummysig),&l);
                    else 
                    {
                        hal_sig_t *sig;
                        sig = SHMPTR(source->signal);
                        set_data_value(source->type, SHMPTR(sig->data_ptr),&l);
                    }
                }
                else if( ta->trigger.type == HAL_SIG )
                {
                    hal_sig_t *source=SHMPTR( ta->trigger.pin );
                    set_data_value(source->type, SHMPTR(source->data_ptr),&l);
                }
                else if( ta->trigger.type == HAL_PARAMETER )
                {
                    hal_param_t *source = SHMPTR( ta->trigger.pin );
                    set_data_value(source->type, SHMPTR(source->data_ptr),&l);
                }
                
                ta->trigger.last.value.u = l.value.u;
                ta->trigger.cmd = ta->request.type;
            }
            else if( ta->request.cmd == OSC_CHECK )
            {
                snprintf(sendBuff, sizeof(sendBuff), "%d\n", ta->trigger.cmd);
                write(connfd, sendBuff, strlen(sendBuff));
            }
            else if( ta->request.cmd == OSC_GET )
            {
            	snprintf(sendBuff, sizeof(sendBuff), "Samples %d thread %d\n",
                	    ta->pointer, thread);
                write(connfd, sendBuff, strlen(sendBuff));
                
                for(int i=0; i<ta->pointer;i++)
                {
                    switch (array[i].type) 
                    {
                        case HAL_BIT:
                        	snprintf(sendBuff, sizeof(sendBuff), "%d %d\n",
                        	    array[i].channel, array[i].value.b);
	                    break;

                        case HAL_FLOAT:
                        	snprintf(sendBuff, sizeof(sendBuff), "%d %f\n",
                        	    array[i].channel, array[i].value.f);
                        break;
                        
                        case HAL_S32:
                        	snprintf(sendBuff, sizeof(sendBuff), "%d %d\n",
                        	    array[i].channel, array[i].value.s);
                        break;
                        
                        case HAL_U32:
                        	snprintf(sendBuff, sizeof(sendBuff), "%d %d\n",
                        	    array[i].channel, array[i].value.u);
                        break;
                        
                        default:
                            /* Shouldn't get here, but just in case... */
                        break;
                    }
                    write(connfd, sendBuff, strlen(sendBuff));
                }
                ta->pointer = 0;
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
    pthread_mutex_unlock(&args->mutex); 
    pthread_join(thread_id,NULL);
    hal_exit(comp_id);
}

static void sample(void *arg, long period)
{
    if( args->pointer < samples && args->trigger.cmd == SAMPLE_RUN )
    {
        for( int i=0; i < channels; i++ )
        {
            if( channel[i].offset != 0 )
            {
                if( channel[i].type == HAL_PIN )
                {
                    hal_pin_t *source=SHMPTR( channel[i].offset );
                    if (source->signal == 0) 
                        set_data_value(source->type, &(source->dummysig),
                            data+args->pointer);
                    else 
                    {
                        hal_sig_t *sig;
                        sig = SHMPTR(source->signal);
                        set_data_value(source->type, SHMPTR(sig->data_ptr),
                            data+args->pointer);
                    }
                }
                else if( channel[i].type == HAL_SIG )
                {
                    hal_sig_t *source=SHMPTR( channel[i].offset );
                    set_data_value(source->type, SHMPTR(source->data_ptr),
                        data+args->pointer);
                }
                else if( channel[i].type == HAL_PARAMETER )
                {
                    hal_param_t *source = SHMPTR( channel[i].offset );
                    set_data_value(source->type, SHMPTR(source->data_ptr),
                        data+args->pointer);
                }
                else
                    continue;
                    
                data[args->pointer].channel = i;

                args->pointer = args->pointer + 1;

                if( args->pointer == samples )
                    break;
            }
        }
    }
    else if( args->trigger.cmd == SAMPLE_RUN )
    {
        args->trigger.cmd = SAMPLE_COMPLETE;
    }
    else if( args->trigger.cmd == SAMPLE_CHANGE 
            || args->trigger.cmd == SAMPLE_HIGH 
            || args->trigger.cmd == SAMPLE_LOW )
    {
        data_t now;
        data_t last;
        int type;

        memcpy(&last,&args->trigger.last,sizeof(data_t));

        if( args->trigger.type == HAL_PIN )
        {
            hal_pin_t *source=SHMPTR( args->trigger.pin );
            if (source->signal == 0) 
            {
                set_data_value(source->type, &(source->dummysig),&now);
                set_data_value(source->type, &(source->dummysig),&args->trigger.last);
                type = source->type;
            }
            else 
            {
                hal_sig_t *sig;
                sig = SHMPTR(source->signal);
                set_data_value(source->type, SHMPTR(sig->data_ptr),&now);
                set_data_value(source->type, SHMPTR(sig->data_ptr),&args->trigger.last);
                type = source->type;
            }
        }
        else if( args->trigger.type == HAL_SIG )
        {
            hal_sig_t *source=SHMPTR( args->trigger.pin );
            set_data_value(source->type, SHMPTR(source->data_ptr),&now);
            set_data_value(source->type, SHMPTR(source->data_ptr),&args->trigger.last);
            type = source->type;
        }
        else if( args->trigger.type == HAL_PARAMETER )
        {
            hal_param_t *source = SHMPTR( args->trigger.pin );
            set_data_value(source->type, SHMPTR(source->data_ptr),&now);
            set_data_value(source->type, SHMPTR(source->data_ptr),&args->trigger.last);
            type = source->type;
        }          
        else
            return;

        switch(type)
        {
            case HAL_BIT:
            	if ( (now.value.b >= args->trigger.value) != 
            	    (last.value.b >= args->trigger.value) )
            	{
            	    if( args->trigger.cmd == SAMPLE_CHANGE ||
            	        ( args->trigger.cmd == SAMPLE_HIGH && 
            	            now.value.b >= args->trigger.value ) ||
            	        ( args->trigger.cmd == SAMPLE_LOW && 
            	            now.value.b < args->trigger.value ))
            	        args->trigger.cmd = SAMPLE_RUN;
            	}
        	break;
        
            case HAL_FLOAT:
            	if ( (now.value.f >= args->trigger.value) != 
            	    (last.value.f >= args->trigger.value) )
            	{
            	    if( args->trigger.cmd == SAMPLE_CHANGE ||
            	        ( args->trigger.cmd == SAMPLE_HIGH && 
            	            now.value.f >= args->trigger.value ) ||
            	        ( args->trigger.cmd == SAMPLE_LOW && 
            	            now.value.f < args->trigger.value ))
            	        args->trigger.cmd = SAMPLE_RUN;
            	}
	        break;
            
            case HAL_S32:
            	if ( (now.value.s >= args->trigger.value) != 
            	    (last.value.s >= args->trigger.value) )
            	{
            	    if( args->trigger.cmd == SAMPLE_CHANGE ||
            	        ( args->trigger.cmd == SAMPLE_HIGH && 
            	            now.value.s >= args->trigger.value ) ||
            	        ( args->trigger.cmd == SAMPLE_LOW && 
            	            now.value.s < args->trigger.value ))
            	        args->trigger.cmd = SAMPLE_RUN;
            	}
	        break;
            
            case HAL_U32:
            	if ( (now.value.u >= args->trigger.value) != 
            	    (last.value.u >= args->trigger.value) )
            	{
            	    if( args->trigger.cmd == SAMPLE_CHANGE ||
            	        ( args->trigger.cmd == SAMPLE_HIGH && 
            	            now.value.u >= args->trigger.value ) ||
            	        ( args->trigger.cmd == SAMPLE_LOW &&
            	            now.value.u < args->trigger.value ))
            	        args->trigger.cmd = SAMPLE_RUN;
            	}
	        break;
            
            default:
	            // Shouldn't get here, but just in case... 
            break;
        }
    }
}

void set_data_value(int type, void *valptr, data_t *structptr)
{
    structptr->type = type;
    switch (type) 
    {
        case HAL_BIT:
        	if (*((char *) valptr) == 0)
	            structptr->value.b = 0;
        	else
	            structptr->value.b = 1;
    	break;
    
        case HAL_FLOAT:
	        structptr->value.f = (double)*((hal_float_t *) valptr);
	    break;
        
        case HAL_S32:
	        structptr->value.s = (long)*((hal_s32_t *) valptr);
	    break;
        
        case HAL_U32:
	        structptr->value.u = (unsigned long)*((hal_u32_t *) valptr);
	    break;
        
        default:
	        /* Shouldn't get here, but just in case... */
        break;
    }
}

static char *get_data_value(int type, void *valptr)
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

int need_quit(pthread_mutex_t *mtx)
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