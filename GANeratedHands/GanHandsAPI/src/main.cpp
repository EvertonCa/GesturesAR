// Kara.cpp : Defines the entry point for the console application.
//

#include "Kara.hpp"

#include "opencv2/opencv.hpp"
#include <opencv2/core.hpp>
#include <opencv2/highgui.hpp>

#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <limits.h>
#include <string>
#include <iostream>
#include <sstream>
#include <semaphore.h>

#define FILENAME_MESSAGE_HANDS "/tmp/blockhands"
#define MESSAGE_BLOCK_SIZE 4096
#define FILENAME_CAM "/tmp/blockcamhands"
#define IPC_RESULT_ERROR (-1)
#define HANDS_SEM_CAM_PRODUCER_FNAME "/handscamproducer"
#define HANDS_SEM_CAM_CONSUMER_FNAME "/handscamconsumer"
#define HANDS_SEM_MESSAGE_PRODUCER_FNAME "/handsmesproducer"
#define HANDS_SEM_MESSAGE_CONSUMER_FNAME "/handsmesconsumer"
#define CAMERA_HEIGHT 1080
#define CAMERA_WIDTH 1920
#define CAMERA_CHANNELS 3
#define CAMERA_BLOCK_SIZE (CAMERA_WIDTH*CAMERA_HEIGHT*CAMERA_CHANNELS)
#define CAMERA_REFRESH_RATE 30
#define RESTART_THRESHOLD 1000.0

static int get_shared_block(char *filename, int size) {
    key_t key;

    // request a key
    // the key is linked to a filename, so that other programs can access it
    if (-1 != open(filename, O_CREAT, 0777)) {
        key = key = ftok(filename, 0);
    } else {
        perror("open");
        exit(1);
    }

    if (key == IPC_RESULT_ERROR) {
        return IPC_RESULT_ERROR;
    }

    // get shared block --- create it if it doesn't exist
    return shmget(key, size, IPC_CREAT | SHM_R | SHM_W );
}

char * attach_memory_block(char *filename, int size) {
    int shared_block_id = get_shared_block(filename, size);
    char *result;

    if (shared_block_id == IPC_RESULT_ERROR) {
        return NULL;
    }

    //map the shared block int this process's memory and give me a pointer to it
    result = (char*) shmat(shared_block_id, NULL, 0);
    if (result == (char *)IPC_RESULT_ERROR) {
        return NULL;
    }

    return result;
}

bool detach_memory_block(char *block) {
    return (shmdt(block) != IPC_RESULT_ERROR);
}

bool destroy_memory_block(char *filename) {
    int shared_block_id = get_shared_block(filename, 0);

    if (shared_block_id == IPC_RESULT_ERROR) {
        return NULL;
    }

    return (shmctl(shared_block_id, IPC_RMID, NULL) != IPC_RESULT_ERROR);
}

bool check3D(std::vector<cv::Point3d> *coordinates3d) {
	for (int i = 0; i < coordinates3d->size(); i++){
		if (coordinates3d->at(i).z > RESTART_THRESHOLD || coordinates3d->at(i).z < -RESTART_THRESHOLD ){
			return false;
		}
	}
	return true;

}

bool run(sem_t *sem_prod_cam, sem_t *sem_cons_cam, sem_t *sem_prod_message, sem_t *sem_cons_message, char *block_cam, char *block_message, int *frame_cont) {
	
	Kara kara;

    cv::Mat frame;

    bool whileContinue = true;

	while(whileContinue)
	{

		// HANDLING CAMERA FEED AND PROCESSING
		sem_wait(sem_prod_cam); // wait for the producer to have an open slot

        frame = cv::Mat(CAMERA_HEIGHT, CAMERA_WIDTH, 16, block_cam, CAMERA_CHANNELS * CAMERA_WIDTH); // creates a frame from memory

        cv::Mat temp;

        temp = frame;

        kara.processImg(temp);

        sem_post(sem_cons_cam); // signal that data was acquired

        (*frame_cont) ++;

        // HANDLING MESSAGES
        sem_wait(sem_cons_message); // wait for the consumer to have an open slot

        std::vector<cv::Point3d> coordinates3d = kara.getCurrent3D();

        bool answer = check3D(&coordinates3d);

        std::stringstream coordinatesString;

        for (int i = 0; i < 26; ++i)
        {
            if (i % 5 != 2){
                coordinatesString << coordinates3d[i];
            }
        }

        coordinatesString << std::endl;

        //std::cout << coordinatesString.str().c_str() << std::endl;

        strncpy(block_message, coordinatesString.str().c_str(), MESSAGE_BLOCK_SIZE);

        sem_post(sem_prod_message); // signal that something is in memory

        if (!answer)
        	return false;
		

		int waitKeyPressed = cv::waitKey(1000/30);

		if ( waitKeyPressed >= 0) {
			if (waitKeyPressed == 27) { // if "ESQ" is pressed, the program ends.
        		whileContinue = false;
			} else if (waitKeyPressed == 82 || waitKeyPressed == 114){ // if "R" is pressed, resets the bb and the skeleton (will not reset 3D)
				//kara.resetSkeleton();
				//kara.rescaleSkeleton();
				//kara.resetBoundingBox();
				return false;
			}
    	}
    }

	return true;
}


int main()
{

	//cv::namedWindow("GANHands Cam", cv::WINDOW_AUTOSIZE);

	// setup some semaphores
    sem_t *sem_prod_cam = sem_open(HANDS_SEM_CAM_PRODUCER_FNAME, 0);
    if (sem_prod_cam == SEM_FAILED) {
        perror("sem_open/handscamproducer");
        exit(EXIT_FAILURE);
    }

    sem_t *sem_cons_cam = sem_open(HANDS_SEM_CAM_CONSUMER_FNAME, 1);
    if (sem_cons_cam == SEM_FAILED) {
        perror("sem_open/handscamconsumer");
        exit(EXIT_FAILURE);
    }

    sem_t *sem_prod_message = sem_open(HANDS_SEM_MESSAGE_PRODUCER_FNAME, 0);
    if (sem_prod_message == SEM_FAILED) {
        perror("sem_open/handscamproducer");
        exit(EXIT_FAILURE);
    }

    sem_t *sem_cons_message = sem_open(HANDS_SEM_MESSAGE_CONSUMER_FNAME, 1);
    if (sem_cons_message == SEM_FAILED) {
        perror("sem_open/handscamconsumer");
        exit(EXIT_FAILURE);
    }

    // grab the shared memory block_cam
    char *block_cam = attach_memory_block(FILENAME_CAM, CAMERA_BLOCK_SIZE);
    if (block_cam == NULL) {
        printf("ERROR: coundn't get block_cam\n");
        return -1;
    }

    // grab the shared memory block_message
    char *block_message = attach_memory_block(FILENAME_MESSAGE_HANDS, MESSAGE_BLOCK_SIZE);
    if (block_message == NULL) {
        printf("ERROR: coundn't get block_message\n");
        return -1;
    }

    std::cout << " ----------------------------------- STARTING GANHands ---------------------------------------- " << std::endl;

    int frame_cont = 0;

	while(!run(sem_prod_cam, sem_cons_cam, sem_prod_message, sem_cons_message, block_cam, block_message, &frame_cont));

	sem_close(sem_prod_cam);
    sem_close(sem_cons_cam);
    sem_close(sem_prod_message);
    sem_close(sem_cons_message);

    detach_memory_block(block_cam);
    detach_memory_block(block_message);
		
	return 0;
}