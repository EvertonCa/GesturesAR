#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include "shared_memory.h"
#include <unistd.h>
#include <stdio.h>
#include <limits.h>

#define IPC_RESULT_ERROR (-1)

static int get_shared_block(char *filename, int size) {
    key_t key;

    // request a key
    // the key is linked to a filename, so that other programs can access it
    key = ftok(filename, 0);
    if (key == IPC_RESULT_ERROR) {
        return IPC_RESULT_ERROR;
    }

    // get shared block --- create it if it doesn't exist
    return shmget(key, size, 0644 | IPC_CREAT);
}

char * attach_memory_block(char *filename, int size) {
    int shared_block_id = get_shared_block(filename, size);
    char *result;

    if (shared_block_id == IPC_RESULT_ERROR) {
        return NULL;
    }

    //map the shared block int this process's memory and give me a pointer to it
    result = shmat(shared_block_id, NULL, 0);
    if (result == (char *)IPC_RESULT_ERROR) {
        return NULL;
    }

    return result;
}

bool detach_memory_block(char *block) {
    return (shmdt(block) != IPC_RESULT_ERROR);
}

bool destroy_memory_block(char *filename) {
    int shared_block_id = get_shared_block(filename, 0);

    if (shared_block_id == IPC_RESULT_ERROR) {
        return NULL;
    }

    return (shmctl(shared_block_id, IPC_RMID, NULL) != IPC_RESULT_ERROR);
}
