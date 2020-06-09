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
static int comp_id;
hal_data_t *hal_data;
int listenfd = 0;
char sendBuff[1024];
pthread_t thread_id;
socket_req_t request;
pthread_mutex_t mxq;
channels_t *ch;
trigger_t tr;
data_t *data;
int sample_pointer;
        
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

    if( samples == -1 )
        samples = 1000000000/thread;

    data = malloc(sizeof(data_t)*samples);
    ch = malloc(sizeof(channels_t)*channels);
    
    struct sockaddr_in serv_addr;

    memset(&serv_addr, 0, sizeof(serv_addr));
    memset(sendBuff, 0, sizeof(sendBuff));

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

    pthread_mutex_init(&mxq, NULL);
    pthread_mutex_lock(&mxq);

    thread_arg_t arg = { &mxq, &request, ch, &tr, data, &sample_pointer };
    
    if( pthread_create( &thread_id, NULL, connection_handler, &arg ) < 0)
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
    while( !need_quit(mtx))
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
                
            if( ta->request->cmd == OSC_STOP )
            {
                ta->trigger->cmd = SAMPLE_IDLE;
                *(ta->pointer) = 0;
            }
            else if( ta->request->cmd == OSC_LIST )
            {
                if( ta->request->type == HAL_PIN )
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
                else if( ta->request->type == HAL_SIG )
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
                else if( ta->request->type == HAL_PARAMETER )
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
            else if( ta->request->cmd == OSC_STATE )
            {
                char *value_str;
                if( ta->request->type == HAL_PIN )
                {
                    hal_pin_t *source=SHMPTR(ta->request->value.u);
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
                else if( ta->request->type == HAL_SIG )
                {
                    hal_sig_t *source=SHMPTR(ta->request->value.u);
                    value_str = get_data_value(source->type, SHMPTR(source->data_ptr));
                    snprintf(sendBuff, sizeof(sendBuff), "%s\n",value_str);
                }
                else if( ta->request->type == HAL_PARAMETER )
                {
                    hal_param_t *source = SHMPTR(ta->request->value.u);
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
            else if( ta->request->cmd == OSC_CHANNEL )
            {
                if( ta->request->type/10 < channels )
                {
                    ta->channels[ta->request->type/10].offset = ta->request->value.u;
                    ta->channels[ta->request->type/10].type = ta->request->type%10;
                }
            }
            else if( ta->request->cmd == OSC_TRIG )
            {
                ta->trigger->cmd = SAMPLE_IDLE;
                ta->trigger->type = ta->request->type;
                ta->trigger->pin = ta->request->value.u;
            }
            else if( ta->request->cmd == OSC_RUN )
            {
                *(ta->pointer) = 0;
                
                ta->trigger->value = ta->request->value.f;
                
                data_t l;
                if( ta->trigger->type == HAL_PIN )
                {
                    hal_pin_t *source=SHMPTR( ta->trigger->pin );
                    if (source->signal == 0) 
                        set_data_value(source->type, &(source->dummysig),&l);
                    else 
                    {
                        hal_sig_t *sig;
                        sig = SHMPTR(source->signal);
                        set_data_value(source->type, SHMPTR(sig->data_ptr),&l);
                    }
                }
                else if( ta->trigger->type == HAL_SIG )
                {
                    hal_sig_t *source=SHMPTR( ta->trigger->pin );
                    set_data_value(source->type, SHMPTR(source->data_ptr),&l);
                }
                else if( ta->trigger->type == HAL_PARAMETER )
                {
                    hal_param_t *source = SHMPTR( ta->trigger->pin );
                    set_data_value(source->type, SHMPTR(source->data_ptr),&l);
                }
                
                ta->trigger->last.value.u = l.value.u;
                ta->trigger->cmd = ta->request->type;
            }
            else if( ta->request->cmd == OSC_CHECK )
            {
                snprintf(sendBuff, sizeof(sendBuff), "%d\n", ta->trigger->cmd);
                write(connfd, sendBuff, strlen(sendBuff));
            }
            else if( ta->request->cmd == OSC_GET )
            {
            	snprintf(sendBuff, sizeof(sendBuff), "Samples %d thread %d\n",
                	    *(ta->pointer), thread);
                write(connfd, sendBuff, strlen(sendBuff));
                
                for(int i=0; i<*(ta->pointer);i++)
                {
                    switch (ta->array[i].type) 
                    {
                        case HAL_BIT:
                        	snprintf(sendBuff, sizeof(sendBuff), "%d %d\n",
                        	    ta->array[i].channel, ta->array[i].value.b);
	                    break;

                        case HAL_FLOAT:
                        	snprintf(sendBuff, sizeof(sendBuff), "%d %f\n",
                        	    ta->array[i].channel, ta->array[i].value.f);
                        break;
                        
                        case HAL_S32:
                        	snprintf(sendBuff, sizeof(sendBuff), "%d %d\n",
                        	    ta->array[i].channel, ta->array[i].value.s);
                        break;
                        
                        case HAL_U32:
                        	snprintf(sendBuff, sizeof(sendBuff), "%d %d\n",
                        	    ta->array[i].channel, ta->array[i].value.u);
                        break;
                        
                        default:
                            /* Shouldn't get here, but just in case... */
                        break;
                    }
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

static void sample(void *arg, long period)
{
    if( sample_pointer < samples && tr.cmd == SAMPLE_RUN )
    {
        for( int i=0; i < channels; i++ )
        {
            if( ch[i].offset!=0 )
            {
                if( ch[i].type == HAL_PIN )
                {
                    hal_pin_t *source=SHMPTR( ch[i].offset );
                    if (source->signal == 0) 
                        set_data_value(source->type, &(source->dummysig),
                            data+sample_pointer);
                    else 
                    {
                        hal_sig_t *sig;
                        sig = SHMPTR(source->signal);
                        set_data_value(source->type, SHMPTR(sig->data_ptr),
                            data+sample_pointer);
                    }
                }
                else if( ch[i].type == HAL_SIG )
                {
                    hal_sig_t *source=SHMPTR( ch[i].offset );
                    set_data_value(source->type, SHMPTR(source->data_ptr),
                        data+sample_pointer);
                }
                else if( ch[i].type == HAL_PARAMETER )
                {
                    hal_param_t *source = SHMPTR( ch[i].offset );
                    set_data_value(source->type, SHMPTR(source->data_ptr),
                        data+sample_pointer);
                }
                else
                    continue;
                    
                data[sample_pointer].channel = i;

                sample_pointer++;
                if( sample_pointer == samples )
                    break;
            }
        }
    }
    else if( tr.cmd == SAMPLE_RUN )
    {
        tr.cmd = SAMPLE_COMPLETE;
    }
    else if( tr.cmd == SAMPLE_CHANGE 
            || tr.cmd == SAMPLE_HIGH 
            || tr.cmd == SAMPLE_LOW )
    {
        data_t now;
        data_t last;
        int type;

        memcpy(&last,&tr.last,sizeof(data_t));

        if( tr.type == HAL_PIN )
        {
            hal_pin_t *source=SHMPTR( tr.pin );
            if (source->signal == 0) 
            {
                set_data_value(source->type, &(source->dummysig),&now);
                set_data_value(source->type, &(source->dummysig),&tr.last);
                type = source->type;
            }
            else 
            {
                hal_sig_t *sig;
                sig = SHMPTR(source->signal);
                set_data_value(source->type, SHMPTR(sig->data_ptr),&now);
                set_data_value(source->type, SHMPTR(sig->data_ptr),&tr.last);
                type = source->type;
            }
        }
        else if( tr.type == HAL_SIG )
        {
            hal_sig_t *source=SHMPTR( tr.pin );
            set_data_value(source->type, SHMPTR(source->data_ptr),&now);
            set_data_value(source->type, SHMPTR(source->data_ptr),&tr.last);
            type = source->type;
        }
        else if( tr.type == HAL_PARAMETER )
        {
            hal_param_t *source = SHMPTR( tr.pin );
            set_data_value(source->type, SHMPTR(source->data_ptr),&now);
            set_data_value(source->type, SHMPTR(source->data_ptr),&tr.last);
            type = source->type;
        }          
        else
            return;

        switch(type)
        {
            case HAL_BIT:
            	if ( (now.value.b >= tr.value) != (last.value.b >= tr.value) )
            	{
            	    if( tr.cmd == SAMPLE_CHANGE ||
            	        ( tr.cmd == SAMPLE_HIGH && now.value.b >= tr.value ) ||
            	        ( tr.cmd == SAMPLE_LOW && now.value.b < tr.value ))
            	        tr.cmd = SAMPLE_RUN;
            	}
        	break;
        
            case HAL_FLOAT:
            	if ( (now.value.f >= tr.value) != (last.value.f >= tr.value) )
            	{
            	    if( tr.cmd == SAMPLE_CHANGE ||
            	        ( tr.cmd == SAMPLE_HIGH && now.value.f >= tr.value ) ||
            	        ( tr.cmd == SAMPLE_LOW && now.value.f < tr.value ))
            	        tr.cmd = SAMPLE_RUN;
            	}
	        break;
            
            case HAL_S32:
            	if ( (now.value.s >= tr.value) != (last.value.s >= tr.value) )
            	{
            	    if( tr.cmd == SAMPLE_CHANGE ||
            	        ( tr.cmd == SAMPLE_HIGH && now.value.s >= tr.value ) ||
            	        ( tr.cmd == SAMPLE_LOW && now.value.s < tr.value ))
            	        tr.cmd = SAMPLE_RUN;
            	}
	        break;
            
            case HAL_U32:
            	if ( (now.value.u >= tr.value) != (last.value.u >= tr.value) )
            	{
            	    if( tr.cmd == SAMPLE_CHANGE ||
            	        ( tr.cmd == SAMPLE_HIGH && now.value.u >= tr.value ) ||
            	        ( tr.cmd == SAMPLE_LOW && now.value.u < tr.value ))
            	        tr.cmd = SAMPLE_RUN;
            	}
	        break;
            
            default:
	            /* Shouldn't get here, but just in case... */
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