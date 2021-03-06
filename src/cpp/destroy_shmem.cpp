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
    sem_unlink(SLAM_SEM_CORRECTION_FNAME);
    sem_unlink(SLAM_SEM_PLANE_CONS_FNAME);
    sem_unlink(SLAM_SEM_PLANE_PROD_FNAME);

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

    // setup the CORRECTION semaphores
    sem_t *sem_correction = sem_open(SLAM_SEM_CORRECTION_FNAME, O_CREAT, 0660, 1);
    if (sem_correction == SEM_FAILED) {
        perror("sem_open/correction");
        exit(EXIT_FAILURE);
    }

    // setup the slam plane semaphores
    sem_t *sem_plane_cons = sem_open(SLAM_SEM_PLANE_CONS_FNAME, O_CREAT, 0660, 1);
    if (sem_plane_cons == SEM_FAILED) {
        perror("sem_open/planecons");
        exit(EXIT_FAILURE);
    }

    sem_t *sem_plane_prod = sem_open(SLAM_SEM_PLANE_PROD_FNAME, O_CREAT, 0660, 1);
    if (sem_plane_prod == SEM_FAILED) {
        perror("sem_open/planeprod");
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

    // grab the hands camera feed shared memory block
    char *block_cam_hands = attach_memory_block(FILENAME_CAM_HANDS, CAMERA_BLOCK_SIZE);
    if (block_cam_hands == NULL) {
        printf("ERROR: coundn't get hands camera block\n");
        return -1;
    }

    // grab the correction shared memory block
    char *block_correction = attach_memory_block(FILENAME_CORRECTION_SLAM, MESSAGE_BLOCK_SIZE);
    if (block_correction == NULL) {
        printf("ERROR: coundn't get slam correction block\n");
        return -1;
    }

    // grab the slam plane shared memory block
    char *block_plane = attach_memory_block(FILENAME_SLAM_PLANE, MESSAGE_BLOCK_SIZE);
    if (block_plane == NULL) {
        printf("ERROR: coundn't get slam plane block\n");
        return -1;
    }

    // cleanup
    sem_close(sem_prod_yolo);
    sem_close(sem_cons_yolo);
    sem_close(sem_prod_slam);
    sem_close(sem_cons_slam);
    sem_close(sem_prod_hands);
    sem_close(sem_cons_hands);
    sem_close(sem_correction);
    sem_close(sem_plane_cons);
    sem_close(sem_plane_prod);

    detach_memory_block(block_yolo);
    detach_memory_block(block_slam);
    detach_memory_block(block_hands);
    detach_memory_block(block_correction);
    detach_memory_block(block_cam_hands);
    detach_memory_block(block_plane);

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

    if (destroy_memory_block(FILENAME_CORRECTION_SLAM)) {
        printf("Destroyed block: %s\n", FILENAME_CORRECTION_SLAM);
    } else {
        printf("Could not destroy block: %s\n", FILENAME_CORRECTION_SLAM);
    }

    if (destroy_memory_block(FILENAME_SLAM_PLANE)) {
        printf("Destroyed block: %s\n", FILENAME_SLAM_PLANE);
    } else {
        printf("Could not destroy block: %s\n", FILENAME_SLAM_PLANE);
    }

    return 0;
}

