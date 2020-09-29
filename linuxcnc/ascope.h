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

#define RTAPI
#define LCNC_28

#include <rtapi.h>		/* RTAPI realtime OS API */
#include <rtapi_app.h>		/* RTAPI realtime module decls */
#include <hal.h>		/* HAL public API decls */
#include <stdio.h>	
#include <rtapi_string.h>
#include <rtapi_stdint.h>

#ifdef LCNC_27
#include <rtapi_common.h>
#endif

#include <sys/socket.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <pthread.h>

#define SHMPTR(offset)  ( (void *)( hal_shmem_base + (offset) ) )
#define SHMOFF(ptr)     ( ((char *)(ptr)) - hal_shmem_base )
                       
#define SHMEM_KEY 0x27267382
                       
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

typedef unsigned long rtapi_mutex_t;

#ifdef LCNC_27
typedef int rtapi_intptr_t;
#else
typedef long rtapi_intptr_t;
#endif

typedef struct {
    int version;		/* version code for structs, etc */
    rtapi_mutex_t mutex;	/* protection for linked lists, etc. */
    hal_s32_t shmem_avail;	/* amount of shmem left free */
    constructor pending_constructor;
			/* pointer to the pending constructor function */
    char constructor_prefix[HAL_NAME_LEN+1];
			        /* prefix of name for new instance */
    char constructor_arg[HAL_NAME_LEN+1];
			        /* prefix of name for new instance */
    rtapi_intptr_t shmem_bot;		/* bottom of free shmem (first free byte) */
    rtapi_intptr_t shmem_top;		/* top of free shmem (1 past last free) */
    rtapi_intptr_t comp_list_ptr;		/* root of linked list of components */
    rtapi_intptr_t pin_list_ptr;		/* root of linked list of pins */
    rtapi_intptr_t sig_list_ptr;		/* root of linked list of signals */
    rtapi_intptr_t param_list_ptr;		/* root of linked list of parameters */
    rtapi_intptr_t funct_list_ptr;		/* root of linked list of functions */
    rtapi_intptr_t thread_list_ptr;	/* root of linked list of threads */
    long base_period;		/* timer period for realtime tasks */
    int threads_running;	/* non-zero if threads are started */
    rtapi_intptr_t oldname_free_ptr;	/* list of free oldname structs */
    rtapi_intptr_t comp_free_ptr;		/* list of free component structs */
    rtapi_intptr_t pin_free_ptr;		/* list of free pin structs */
    rtapi_intptr_t sig_free_ptr;		/* list of free signal structs */
    rtapi_intptr_t param_free_ptr;		/* list of free parameter structs */
    rtapi_intptr_t funct_free_ptr;		/* list of free function structs */
    hal_list_t funct_entry_free;	/* list of free funct entry structs */
    rtapi_intptr_t thread_free_ptr;	/* list of free thread structs */
    int exact_base_period;      /* if set, pretend that rtapi satisfied our
				   period request exactly */
    unsigned char lock;         /* hal locking, can be one of the HAL_LOCK_* types */
} hal_data_t;

typedef struct {
    rtapi_intptr_t next_ptr;		/* next pin in linked list */
    int data_ptr_addr;		/* address of pin data pointer */
    int owner_ptr;		/* component that owns this pin */
    int signal;			/* signal to which pin is linked */
    hal_data_u dummysig;	/* if unlinked, data_ptr points here */
    int oldname;		/* old name if aliased, else zero */
    hal_type_t type;		/* data type */
    hal_pin_dir_t dir;		/* pin direction */
    char name[HAL_NAME_LEN + 1];	/* pin name */
} hal_pin_t;

/** HAL 'signal' data structure.
    This structure contains information about a 'signal' object.
*/
typedef struct {
    rtapi_intptr_t next_ptr;		/* next signal in linked list */
    int data_ptr;		/* offset of signal value */
    hal_type_t type;		/* data type */
    int readers;		/* number of input pins linked */
    int writers;		/* number of output pins linked */
    int bidirs;			/* number of I/O pins linked */
    char name[HAL_NAME_LEN + 1];	/* signal name */
} hal_sig_t;

/** HAL 'parameter' data structure.
    This structure contains information about a 'parameter' object.
*/
typedef struct {
    rtapi_intptr_t next_ptr;		/* next parameter in linked list */
    int data_ptr;		/* offset of parameter value */
    int owner_ptr;		/* component that owns this signal */
    int oldname;		/* old name if aliased, else zero */
    hal_type_t type;		/* data type */
    hal_param_dir_t dir;	/* data direction */
    char name[HAL_NAME_LEN + 1];	/* parameter name */
} hal_param_t;

enum CMD {
    OSC_STOP,
    OSC_LIST,
    OSC_STATE,
    OSC_CHANNEL,
    OSC_TRIG,
    OSC_RUN,
    OSC_CHECK,
    OSC_GET
};

enum TRIG {
    SAMPLE_IDLE,
    SAMPLE_RUN,
    SAMPLE_COMPLETE,
    SAMPLE_HIGH,
    SAMPLE_LOW,
    SAMPLE_CHANGE
};

enum HAL_TYPE {
    HAL_PIN,
    HAL_SIG,
    HAL_PARAMETER
};

typedef struct {
    hal_data_u control;
    unsigned int cmd:8;
    unsigned int type:8;
    hal_data_u value;
} socket_req_t;

typedef struct {
    int type;
    int offset;
} channels_t;

typedef struct {
    unsigned int channel:8;
    unsigned int type:8;
    hal_data_u value;
} data_t;

typedef struct {
    int cmd;
    int type;
    int pin;
    float value;
    data_t last;
} trigger_t;

typedef struct {
    int channels;
    int samples;
} thread_arg_size_t;

typedef struct {
    int init;
    pthread_mutex_t mutex;
    socket_req_t request;
    trigger_t trigger;
    int pointer;
} thread_arg_t;

extern char *hal_shmem_base;

void connection_handler(void *arg);
static void sample(void *arg, long period);
void set_data_value(int type, void *valptr, data_t *structptr);
static char *get_data_value(int type, void *valptr);
int need_quit(pthread_mutex_t *mtx);
