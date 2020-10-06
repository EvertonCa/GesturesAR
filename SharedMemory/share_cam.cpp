//
// Created by Everton Cardoso on 01/10/20.
// This program captures live feed from the attached webcam and shares them via shared memory
//

#include "opencv2/opencv.hpp"
#include <opencv2/core.hpp>
#include <opencv2/highgui.hpp>
#include <semaphore.h>
#include <fcntl.h>

#include "shared_memory.h"
#include "camera_parameters.h"
#include "virtual_camera_handler.h"


int main() {
    //cv::namedWindow("Share Cam", cv::WINDOW_AUTOSIZE);
    cv::VideoCapture cap(0);
    if (!cap.isOpened())
        return -1;+

    // setup some semaphores
    sem_unlink(SLAM_SEM_CAM_CONSUMER_FNAME);
    sem_unlink(SLAM_SEM_CAM_PRODUCER_FNAME);
    sem_unlink(YOLO_SEM_CAM_CONSUMER_FNAME);
    sem_unlink(YOLO_SEM_CAM_PRODUCER_FNAME);
    sem_unlink(HANDS_SEM_CAM_CONSUMER_FNAME);
    sem_unlink(HANDS_SEM_CAM_PRODUCER_FNAME);


    sem_t *sem_slam_prod = sem_open(SLAM_SEM_CAM_PRODUCER_FNAME, O_CREAT, 0660, 0);
    if (sem_slam_prod == SEM_FAILED) {
        perror("sem_open/slamcamproducer");
        exit(EXIT_FAILURE);
    }

    sem_t *sem_slam_cons = sem_open(SLAM_SEM_CAM_CONSUMER_FNAME, O_CREAT, 0660, 1);
    if (sem_slam_cons == SEM_FAILED) {
        perror("sem_open/slamcamconsumer");
        exit(EXIT_FAILURE);
    }

    sem_t *sem_yolo_prod = sem_open(YOLO_SEM_CAM_PRODUCER_FNAME, O_CREAT, 0660, 0);
    if (sem_yolo_prod == SEM_FAILED) {
        perror("sem_open/yolocamproducer");
        exit(EXIT_FAILURE);
    }

    sem_t *sem_yolo_cons = sem_open(YOLO_SEM_CAM_CONSUMER_FNAME, O_CREAT, 0660, 1);
    if (sem_yolo_cons == SEM_FAILED) {
        perror("sem_open/yolocamconsumer");
        exit(EXIT_FAILURE);
    }

    sem_t *sem_hands_prod = sem_open(HANDS_SEM_CAM_PRODUCER_FNAME, O_CREAT, 0660, 0);
    if (sem_hands_prod == SEM_FAILED) {
        perror("sem_open/handscamproducer");
        exit(EXIT_FAILURE);
    }

    sem_t *sem_hands_cons = sem_open(HANDS_SEM_CAM_CONSUMER_FNAME, O_CREAT, 0660, 1);
    if (sem_hands_cons == SEM_FAILED) {
        perror("sem_open/handscamconsumer");
        exit(EXIT_FAILURE);
    }

    // grab the shared memory block
    char *block = attach_memory_block(FILENAME_CAM, CAMERA_BLOCK_SIZE);
    if (block == NULL) {
        printf("ERROR: coundn't get block\n");
        return -1;
    }

    // creates the virtual camera handlers
    VirtualCameraHandler virtualCam1(cap, VIRTUAL_WEBCAM_1);
    VirtualCameraHandler virtualCam2(cap, VIRTUAL_WEBCAM_2);

    cv::Mat frame;

    while (true) {

        cap >> frame;

        sem_wait(sem_slam_cons); // wait for the slam consumer to have an open slot
        sem_wait(sem_yolo_cons); // wait for the yolo consumer to have an open slot
        sem_wait(sem_hands_cons); // wait for the hands consumer to have an open slot

        // copy the frame to shared memory
        memcpy(block, frame.ptr(), CAMERA_BLOCK_SIZE);

        // replicate the camera frame to the virtual cameras
        virtualCam1.feedCam();
        virtualCam2.feedCam();

        sem_post(sem_slam_prod); // signal to slam that there is a frame in memory
        sem_post(sem_yolo_prod); // signal to yolo that there is a frame in memory
        sem_post(sem_hands_prod); // signal to hands that there is a frame in memory

        //cv::imshow("Share Cam", frame);

        // runs until ESC key is pressed
        if (cv::waitKey(1000 / CAMERA_REFRESH_RATE) == 27) {
            std::cout << "Share cam quit" << std::endl;
            break;
        }
    }

    // cleanup
    sem_close(sem_slam_cons);
    sem_close(sem_yolo_cons);
    sem_close(sem_hands_cons);
    sem_close(sem_hands_prod);
    sem_close(sem_slam_prod);
    sem_close(sem_yolo_prod);

    detach_memory_block(block);
    return 0;
}