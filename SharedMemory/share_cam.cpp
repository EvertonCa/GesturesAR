//
// Created by Everton Cardoso on 01/10/20.
// This program captures live feed from the attached webcam and shares them via shared memory
//

#include "opencv2/opencv.hpp"
#include <opencv2/core.hpp>
#include <opencv2/highgui.hpp>
#include <semaphore.h>

#include "shared_memory.h"
#include "camera_parameters.h"


int main(int, char**) {
    cv::namedWindow("Share Cam", cv::WINDOW_AUTOSIZE);
    cv::VideoCapture cap(0);
    if (!cap.isOpened())
        return -1;

    // setup some semaphores
    sem_t *sem_prod = sem_open(CAM_SEM_PRODUCER_FNAME, 0);
    if (sem_prod == SEM_FAILED) {
        perror("sem_open/camproducer");
        exit(EXIT_FAILURE);
    }

    sem_t *sem_cons = sem_open(CAM_SEM_CONSUMER_FNAME, 1);
    if (sem_cons == SEM_FAILED) {
        perror("sem_open/camconsumer");
        exit(EXIT_FAILURE);
    }

    // grab the shared memory block
    char *block = attach_memory_block(FILENAME, BLOCK_SIZE);
    if (block == NULL) {
        printf("ERROR: coundn't get block\n");
        return -1;
    }

    cv::Mat frame;

    while (true) {

        cap >> frame;

        sem_wait(sem_cons); // wait for the consumer to have an open slot
        memcpy(block, frame.ptr(), BLOCK_SIZE); // copy the frame to shared memory
        sem_post(sem_prod); // signal that something is in memory

        cv::imshow("Share Cam", frame);

        // runs until ESC key is pressed
        if (cv::waitKey(1000/REFRESH_RATE) == 27) {
            std::cout << "share" << std::endl;
            break;
        }
    }

    // cleanup
    sem_close(sem_prod);
    sem_close(sem_cons);
    detach_memory_block(block);
    return 0;
}