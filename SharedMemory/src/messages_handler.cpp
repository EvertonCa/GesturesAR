//
// Created by Everton Cardoso on 09/10/20.
//

#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <semaphore.h>
#include <fcntl.h>

#include "../includes/shared_memory.h"

int main() {

    // unlink possible leftovers
    sem_unlink(YOLO_SEM_MESSAGE_PRODUCER_FNAME);
    sem_unlink(YOLO_SEM_MESSAGE_CONSUMER_FNAME);
    sem_unlink(SLAM_SEM_MESSAGE_PRODUCER_FNAME);
    sem_unlink(SLAM_SEM_MESSAGE_CONSUMER_FNAME);
    sem_unlink(HANDS_SEM_MESSAGE_PRODUCER_FNAME);
    sem_unlink(HANDS_SEM_MESSAGE_CONSUMER_FNAME);

    // setup the YOLO semaphores
    sem_t *sem_prod_yolo = sem_open(YOLO_SEM_MESSAGE_PRODUCER_FNAME, O_CREAT, 0660, 0);
    if (sem_prod_yolo == SEM_FAILED) {
        perror("sem_open/yolocamproducer");
        exit(EXIT_FAILURE);
    }

    sem_t *sem_cons_yolo = sem_open(YOLO_SEM_MESSAGE_CONSUMER_FNAME, O_CREAT, 0660, 1);
    if (sem_cons_yolo == SEM_FAILED) {
        perror("sem_open/yolocamconsumer");
        exit(EXIT_FAILURE);
    }

    // setup the SLAM semaphores
    sem_t *sem_prod_slam = sem_open(SLAM_SEM_MESSAGE_PRODUCER_FNAME, O_CREAT, 0660, 0);
    if (sem_prod_slam == SEM_FAILED) {
        perror("sem_open/slamcamproducer");
        exit(EXIT_FAILURE);
    }

    sem_t *sem_cons_slam = sem_open(SLAM_SEM_MESSAGE_CONSUMER_FNAME, O_CREAT, 0660, 1);
    if (sem_cons_slam == SEM_FAILED) {
        perror("sem_open/slamcamconsumer");
        exit(EXIT_FAILURE);
    }

    // setup the HANDS semaphores
    sem_t *sem_prod_hands = sem_open(HANDS_SEM_MESSAGE_PRODUCER_FNAME, O_CREAT, 0660, 0);
    if (sem_prod_hands == SEM_FAILED) {
        perror("sem_open/handscamproducer");
        exit(EXIT_FAILURE);
    }

    sem_t *sem_cons_hands = sem_open(HANDS_SEM_MESSAGE_CONSUMER_FNAME, O_CREAT, 0660, 1);
    if (sem_cons_hands == SEM_FAILED) {
        perror("sem_open/handscamconsumer");
        exit(EXIT_FAILURE);
    }


    // grab the YOLO shared memory block
    char *block_yolo = attach_memory_block(FILENAME_MESSAGE_YOLO, MESSAGE_BLOCK_SIZE);
    if (block_yolo == NULL) {
        printf("ERROR: coundn't get YOLO block\n");
        return -1;
    }

    // grab the SLAM shared memory block
    char *block_slam = attach_memory_block(FILENAME_MESSAGE_SLAM, MESSAGE_BLOCK_SIZE);
    if (block_slam == NULL) {
        printf("ERROR: coundn't get SLAM block\n");
        return -1;
    }

    // grab the HANDS shared memory block
    char *block_hands = attach_memory_block(FILENAME_MESSAGE_HANDS, MESSAGE_BLOCK_SIZE);
    if (block_hands == NULL) {
        printf("ERROR: coundn't get HANDS block\n");
        return -1;
    }

    while (true) {

        sem_wait(sem_prod_yolo);
        sem_wait(sem_prod_slam);
        sem_wait(sem_prod_hands);

        if (strlen(block_yolo) > 0) {
            printf("YOLO: %s\n", block_yolo);
            bool done = (strcmp(block_yolo, "quit") == 0);
            block_yolo[0] = 0;
            if (done) {
                break;
            }
        }

        if (strlen(block_slam) > 0) {
            printf("SLAM: %s\n", block_slam);
            bool done = (strcmp(block_slam, "quit") == 0);
            block_slam[0] = 0;
            if (done) {
                break;
            }
        }

        if (strlen(block_hands) > 0) {
            printf("GANHands: %s\n", block_hands);
            bool done = (strcmp(block_hands, "quit") == 0);
            block_hands[0] = 0;
            if (done) {
                break;
            }
        }

        sem_post(sem_cons_yolo);
        sem_post(sem_cons_slam);
        sem_post(sem_cons_hands);

    }

    // cleanup
    sem_close(sem_prod_yolo);
    sem_close(sem_cons_yolo);
    sem_close(sem_prod_slam);
    sem_close(sem_cons_slam);
    sem_close(sem_prod_hands);
    sem_close(sem_cons_hands);
    detach_memory_block(block_yolo);
    detach_memory_block(block_slam);
    detach_memory_block(block_hands);

    return 0;
}