//
// Created by Everton Cardoso on 01/10/20.
//
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../includes/shared_memory.h"

int main() {

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

    return 0;
}

