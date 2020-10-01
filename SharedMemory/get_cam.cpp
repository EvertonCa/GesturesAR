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

int main(int argc, char *argv[]) {

    cv::namedWindow("Get Cam", cv::WINDOW_AUTOSIZE);

    // setup some semaphores
    sem_unlink(CAM_SEM_CONSUMER_FNAME);
    sem_unlink(CAM_SEM_PRODUCER_FNAME);

    sem_t *sem_prod = sem_open(CAM_SEM_PRODUCER_FNAME, O_CREAT, 0660, 0);
    if (sem_prod == SEM_FAILED) {
        perror("sem_open/camproducer");
        exit(EXIT_FAILURE);
    }

    sem_t *sem_cons = sem_open(CAM_SEM_CONSUMER_FNAME, O_CREAT, 0660, 1);
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

        sem_wait(sem_prod); // wait for the producer to have an open slot
        frame = cv::Mat(HEIGHT, WIDTH, 16, block, CHANNELS*WIDTH); // creates a frame from memory
        sem_post(sem_cons); // signal that data was acquired

        cv::imshow("Get Cam", frame);

        // runs until ESC key is pressed
        if (cv::waitKey(1000/REFRESH_RATE)  == 27) {
            std::cout << "get" << std::endl;
            break;
        }
    }

    // cleanup
    sem_close(sem_cons);
    sem_close(sem_prod);
    detach_memory_block(block);

    return 0;
}
