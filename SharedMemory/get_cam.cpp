//
// Created by Everton Cardoso on 01/10/20.
//
#include "opencv2/opencv.hpp"
#include <opencv2/core.hpp>
#include <opencv2/highgui.hpp>
#include <stdio.h>
#include <stdlib.h>
#include <semaphore.h>
#include <fcntl.h>

#include "shared_memory.h"

#define HEIGHT 720
#define WIDTH 1280
#define CHANNELS 3
#define BLOCK_SIZE (WIDTH*HEIGHT*CHANNELS)

int main(int argc, char *argv[]) {

    cv::namedWindow("Video", cv::WINDOW_AUTOSIZE);

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

    for ( ; ; ) {

        sem_wait(sem_prod);
        frame = cv::Mat(HEIGHT, WIDTH, 16, block, CHANNELS*WIDTH);
        sem_post(sem_cons);

        cv::imshow("Video", frame);
        if (cv::waitKey(33) >= 0) break;
    }

    sem_close(sem_cons);
    sem_close(sem_prod);
    detach_memory_block(block);

    return 0;
}
