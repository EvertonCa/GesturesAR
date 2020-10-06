//
// Created by Everton Cardoso on 01/10/20.
// This program gets the webcam live feed via shared memory
//
#include "opencv2/opencv.hpp"
#include <opencv2/core.hpp>
#include <opencv2/highgui.hpp>
#include <semaphore.h>
#include <fcntl.h>

#include "shared_memory.h"
#include "camera_parameters.h"

int main() {

    cv::namedWindow("YOLO Get Cam", cv::WINDOW_AUTOSIZE);

    // setup some semaphores
    sem_t *sem_prod_cam = sem_open(YOLO_SEM_CAM_PRODUCER_FNAME, 0);
    if (sem_prod_cam == SEM_FAILED) {
        perror("sem_open/yolocamproducer");
        exit(EXIT_FAILURE);
    }

    sem_t *sem_cons_cam = sem_open(YOLO_SEM_CAM_CONSUMER_FNAME, 1);
    if (sem_cons_cam == SEM_FAILED) {
        perror("sem_open/yolocamconsumer");
        exit(EXIT_FAILURE);
    }

    sem_t *sem_prod_message = sem_open(YOLO_SEM_MESSAGE_PRODUCER_FNAME, 0);
    if (sem_prod_message == SEM_FAILED) {
        perror("sem_open/yolocamproducer");
        exit(EXIT_FAILURE);
    }

    sem_t *sem_cons_message = sem_open(YOLO_SEM_MESSAGE_CONSUMER_FNAME, 1);
    if (sem_cons_message == SEM_FAILED) {
        perror("sem_open/yolocamconsumer");
        exit(EXIT_FAILURE);
    }

    // grab the shared memory block_cam
    char *block_cam = attach_memory_block(FILENAME_CAM, CAMERA_BLOCK_SIZE);
    if (block_cam == NULL) {
        printf("ERROR: coundn't get block_cam\n");
        return -1;
    }

    // grab the shared memory block_message
    char *block_message = attach_memory_block(FILENAME_MESSAGE_YOLO, MESSAGE_BLOCK_SIZE);
    if (block_message == NULL) {
        printf("ERROR: coundn't get block_message\n");
        return -1;
    }

    cv::Mat frame;

    while (true) {

        sem_wait(sem_prod_cam); // wait for the producer to have an open slot
        frame = cv::Mat(CAMERA_HEIGHT, CAMERA_WIDTH, 16, block_cam, CAMERA_CHANNELS * CAMERA_WIDTH); // creates a frame from memory
        sem_post(sem_cons_cam); // signal that data was acquired

        cv::imshow("YOLO Get Cam", frame);

        sem_wait(sem_cons_message); // wait for the consumer to have an open slot
        printf("Writing YOLO\n");
        strncpy(block_message, "YOLO", MESSAGE_BLOCK_SIZE);
        sem_post(sem_prod_message); // signal that something is in memory

        // runs until ESC key is pressed
        if (cv::waitKey(1000 / CAMERA_REFRESH_RATE) == 27) {
            std::cout << "yolo get" << std::endl;
            break;
        }
    }

    return 0;
}
