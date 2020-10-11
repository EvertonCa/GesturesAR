//
// Created by Everton Cardoso on 09/10/20.
//

#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <semaphore.h>
#include <fcntl.h>

#include <thread>

#include "../includes/shared_memory.h"

// this function gets the message for the received sender
void get_message(sem_t *sem_prod, sem_t *sem_cons, char *block, char *modulo) {
    while (true) {
        sem_wait(sem_prod);

        if (strlen(block) > 0) {
            printf("%s: %s\n", modulo, block);
            bool done = (strcmp(block, "quit") == 0);
            block[0] = 0;
            if (done) {
                break;
            }
        }

        sem_post(sem_cons);
    }
}

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

    // creates threads for each module
    char *yoloText = "YOLO";
    char *slamText = "SLAM";
    char *handsText = "HANDS";
    std::thread yoloThread(get_message, sem_prod_yolo, sem_cons_yolo, block_yolo, yoloText);
    std::thread slamThread(get_message, sem_prod_slam, sem_cons_slam, block_slam, slamText);
    std::thread handsThread(get_message, sem_prod_hands, sem_cons_hands, block_hands, handsText);

    // Wait for the threads to finish
    yoloThread.join();
    slamThread.join();
    handsThread.join();

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

}