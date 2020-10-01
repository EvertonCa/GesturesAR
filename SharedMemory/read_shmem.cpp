//
// Created by Everton Cardoso on 01/10/20.
//
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <semaphore.h>
#include <fcntl.h>

#include "shared_memory.h"

int main(int argc, char *argv[]) {

    if (argc != 1) {
        printf("usage - %s //no args", argv[0]);
        return -1;
    }

    // setup some semaphores
    sem_unlink(SEM_CONSUMER_FNAME);
    sem_unlink(SEM_PRODUCER_FNAME);

    sem_t *sem_prod = sem_open(SEM_PRODUCER_FNAME, O_CREAT, 0660, 0);
    if (sem_prod == SEM_FAILED) {
        perror("sem_open/producer");
        exit(EXIT_FAILURE);
    }

    sem_t *sem_cons = sem_open(SEM_CONSUMER_FNAME, O_CREAT, 0660, 1);
    if (sem_cons == SEM_FAILED) {
        perror("sem_open/consumer");
        exit(EXIT_FAILURE);
    }

    // grab the shared memory block
    char *block = attach_memory_block(FILENAME, BLOCK_SIZE);
    if (block == NULL) {
        printf("ERROR: coundn't get block\n");
        return -1;
    }

    while (true) {
        sem_wait(sem_prod);
        if (strlen(block) > 0) {
            printf("Reading: \"%s\"\n", block);
            bool done = (strcmp(block, "quit") == 0);
            block[0] = 0;
            if (done) {
                break;
            }
        }
        sem_post(sem_cons);
    }

    sem_close(sem_cons);
    sem_close(sem_prod);
    detach_memory_block(block);

    return 0;
}
