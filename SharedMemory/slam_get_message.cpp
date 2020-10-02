//
// Created by Everton Cardoso on 02/10/20.
//
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <semaphore.h>
#include <fcntl.h>

#include "shared_memory.h"

int main() {

    sem_unlink(SLAM_SEM_MESSAGE_PRODUCER_FNAME);
    sem_unlink(SLAM_SEM_MESSAGE_CONSUMER_FNAME);

    // setup some semaphores
    sem_t *sem_prod = sem_open(SLAM_SEM_MESSAGE_PRODUCER_FNAME, O_CREAT, 0660, 0);
    if (sem_prod == SEM_FAILED) {
        perror("sem_open/slamcamproducer");
        exit(EXIT_FAILURE);
    }

    sem_t *sem_cons = sem_open(SLAM_SEM_MESSAGE_CONSUMER_FNAME, O_CREAT, 0660, 1);
    if (sem_cons == SEM_FAILED) {
        perror("sem_open/slamcamconsumer");
        exit(EXIT_FAILURE);
    }

    // grab the shared memory block
    char *block = attach_memory_block(FILENAME_MESSAGE_SLAM, MESSAGE_BLOCK_SIZE);
    if (block == NULL) {
        printf("ERROR: coundn't get block\n");
        return -1;
    }

    while (true) {
        sem_wait(sem_prod);
        if (strlen(block) > 0) {
            printf("Reading SLAM: \"%s\"\n", block);
            bool done = (strcmp(block, "quit") == 0);
            block[0] = 0;
            if (done) {
                break;
            }
        }
        sem_post(sem_cons);
    }

    sem_close(sem_prod);
    sem_close(sem_cons);
    detach_memory_block(block);

    return 0;
}