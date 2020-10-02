//
// Created by Everton Cardoso on 01/10/20.
//

#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include "shared_memory.h"
#include <unistd.h>
#include <stdio.h>
#include <limits.h>
#include <fcntl.h>

static int get_shared_block(char *filename, int size) {
    key_t key;

//    char cwd[PATH_MAX];
//    if (getcwd(cwd, sizeof(cwd)) != NULL) {
//        printf("Current working dir: %s\n", cwd);
//    }

    // request a key
    // the key is linked to a filename, so that other programs can access it
    if (-1 != open(filename, O_CREAT, 0777)) {
        key = key = ftok(filename, 0);
    } else {
        perror("open");
        exit(1);
    }

    printf("key: %d\n", key);
    if (key == IPC_RESULT_ERROR) {
        return IPC_RESULT_ERROR;
    }

    // get shared block --- create it if it doesn't exist
    return shmget(key, size, IPC_CREAT | SHM_R | SHM_W);
}

char * attach_memory_block(char *filename, int size) {
    int shared_block_id = get_shared_block(filename, size);
    printf("shared block id: %d\n", shared_block_id);
    char *result;

    if (shared_block_id == IPC_RESULT_ERROR) {
        return NULL;
    }

    //map the shared block int this process's memory and give me a pointer to it
    result = (char*) shmat(shared_block_id, NULL, 0);
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

