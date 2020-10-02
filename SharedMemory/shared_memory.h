//
// Created by Everton Cardoso on 01/10/20.
//

#ifndef SHAREDMEMORYC___SHARED_MEMORY_H
#define SHAREDMEMORYC___SHARED_MEMORY_H

#include <stdbool.h>

#define IPC_RESULT_ERROR (-1)

//attach a shared memory block associated with filename. Create it if doesn't exist
char * attach_memory_block(char *filename, int size);
bool detach_memory_block(char *block);
bool destroy_memory_block(char *filename);

//all of the programs will shared these values
#define BLOCK_SIZE 4096
#define FILENAME_CAM "../share_cam.cpp"
#define FILENAME_MESSAGE_SLAM "../slam_get_message.cpp"
#define FILENAME_MESSAGE_YOLO "../yolo_get_message.cpp"
#define IPC_RESULT_ERROR (-1)

//filenames for two semaphores
#define SEM_PRODUCER_FNAME "/myproducer"
#define SEM_CONSUMER_FNAME "/myconsumer"

//filenames for camera semaphores
#define SLAM_SEM_CAM_PRODUCER_FNAME "/slamcamproducer"
#define SLAM_SEM_CAM_CONSUMER_FNAME "/slamcamconsumer"

#define YOLO_SEM_CAM_PRODUCER_FNAME "/yolocamproducer"
#define YOLO_SEM_CAM_CONSUMER_FNAME "/yolocamconsumer"

//filenames for messages semaphores
#define SLAM_SEM_MESSAGE_PRODUCER_FNAME "/slammesproducer"
#define SLAM_SEM_MESSAGE_CONSUMER_FNAME "/slammesconsumer"

#define YOLO_SEM_MESSAGE_PRODUCER_FNAME "/yolomesproducer"
#define YOLO_SEM_MESSAGE_CONSUMER_FNAME "/yolomesconsumer"

#endif //SHAREDMEMORYC___SHARED_MEMORY_H
