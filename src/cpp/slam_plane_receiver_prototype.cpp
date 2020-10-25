//
// Created by Everton Cardoso on 25/10/20.
//

#include <algorithm>
#include <chrono>
#include <semaphore.h>
#include <fcntl.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <iostream>
#include <string.h>

#define IPC_RESULT_ERROR (-1)
#define MESSAGE_BLOCK_SIZE 4096
#define FILENAME_SLAM_PLANE "/tmp/blockslamplane"
#define SLAM_SEM_PLANE_CONS_FNAME "/slamplanecons"
#define SLAM_SEM_PLANE_PROD_FNAME "/slamplaneprod"

int main() {

    sem_t *sem_slam_plane_cons = sem_open(SLAM_SEM_PLANE_CONS_FNAME, 0);
    if (sem_slam_plane_cons == SEM_FAILED) {
        perror("sem_open/planecons");
        exit(EXIT_FAILURE);
    }

    sem_t *sem_slam_plane_prod = sem_open(SLAM_SEM_PLANE_PROD_FNAME, 1);
    if (sem_slam_plane_cons == SEM_FAILED) {
        perror("sem_open/planeprod");
        exit(EXIT_FAILURE);
    }

    // PLANE SHARED MEMORY
    key_t keyPlane;
    // request a key
    // the key is linked to a filename, so that other programs can access it
    if (-1 != open(FILENAME_SLAM_PLANE, O_CREAT, 0777)) {
        keyPlane = keyPlane = ftok(FILENAME_SLAM_PLANE, 0);
    } else {
        perror("open");
        exit(1);
    }

    // get shared block --- create it if it doesn't exist
    int shared_plane_block_id = shmget(keyPlane, MESSAGE_BLOCK_SIZE, IPC_CREAT | SHM_R | SHM_W );

    char *result_plane;

    if (shared_plane_block_id == IPC_RESULT_ERROR) {
        result_plane = NULL;
    }

    //map the shared block int this process's memory and give me a pointer to it
    result_plane = (char*) shmat(shared_plane_block_id, NULL, 0);
    if (result_plane == (char *)IPC_RESULT_ERROR) {
        result_plane = NULL;
    }

    while (true) {
        sem_wait(sem_slam_plane_cons);

        if (strlen(result_plane) > 0) {
            printf("\"%s\"\n", result_plane);
        } else {
            printf("\"None\"\n");
        }

        sem_post(sem_slam_plane_prod);
    }

}