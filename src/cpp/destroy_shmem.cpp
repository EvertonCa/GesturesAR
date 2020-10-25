//
// Created by Everton Cardoso on 01/10/20.
//
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <semaphore.h>
#include <fcntl.h>

#include "../includes/shared_memory.h"
#include "../includes/camera_parameters.h"

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

    // grab the shared memory block
    char *block = attach_memory_block(FILENAME_CAM, CAMERA_BLOCK_SIZE);
    if (block == NULL) {
        printf("ERROR: coundn't get camera block\n");
        return -1;
    }

    char *block_cam_hands = attach_memory_block(FILENAME_CAM_HANDS, CAMERA_BLOCK_SIZE);
    if (block_cam_hands == NULL) {
        printf("ERROR: coundn't get hands camera block\n");
        return -1;
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
    detach_memory_block(block_cam_hands);

    if (destroy_memory_block(FILENAME_CAM)) {
        printf("Destroyed block: %s\n", FILENAME_CAM);
    } else {
        printf("Could not destroy block: %s\n", FILENAME_CAM);
    }

    if (destroy_memory_block(FILENAME_MESSAGE_SLAM)) {
        printf("Destroyed block: %s\n", FILENAME_MESSAGE_SLAM);
    } else {
        printf("Could not destroy block: %s\n", FILENAME_MESSAGE_SLAM);
    }

    if (destroy_memory_block(FILENAME_MESSAGE_YOLO)) {
        printf("Destroyed block: %s\n", FILENAME_MESSAGE_YOLO);
    } else {
        printf("Could not destroy block: %s\n", FILENAME_MESSAGE_YOLO);
    }

    if (destroy_memory_block(FILENAME_MESSAGE_HANDS)) {
        printf("Destroyed block: %s\n", FILENAME_MESSAGE_HANDS);
    } else {
        printf("Could not destroy block: %s\n", FILENAME_MESSAGE_HANDS);
    }

    if (destroy_memory_block(FILENAME_CAM_HANDS)) {
        printf("Destroyed block: %s\n", FILENAME_CAM_HANDS);
    } else {
        printf("Could not destroy block: %s\n", FILENAME_CAM_HANDS);
    }

    return 0;
}

