//
// Created by Everton Cardoso on 01/10/20.
//

#ifndef SHAREDMEMORYC___SHARED_MEMORY_H
#define SHAREDMEMORYC___SHARED_MEMORY_H

#include <stdbool.h>

//attach a shared memory block associated with filename. Create it if doesn't exist
char * attach_memory_block(char *filename, int size);
bool detach_memory_block(char *block);
bool destroy_memory_block(char *filename);

//all of the programs will shared these values
#define BLOCK_SIZE 4096
#define FILENAME "../write_shmem.cpp"
#define IPC_RESULT_ERROR (-1)

//filenames for two semaphores
#define SEM_PRODUCER_FNAME "/myproducer"
#define SEM_CONSUMER_FNAME "/myconsumer"

#endif //SHAREDMEMORYC___SHARED_MEMORY_H
