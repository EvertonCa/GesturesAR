//
// Created by Everton Cardoso on 23/10/20.
//

#include <algorithm>
#include <chrono>
#include <semaphore.h>
#include <fcntl.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <iostream>
#include <unistd.h>

#define IPC_RESULT_ERROR (-1)
#define MESSAGE_BLOCK_SIZE 4096
#define FILENAME_CORRECTION_SLAM "/tmp/blockslamcorrection"
#define SLAM_SEM_CORRECTION_FNAME "/correction"

int main() {

    sem_unlink(SLAM_SEM_CORRECTION_FNAME);

    // setup some semaphores
    sem_t *sem_correction = sem_open(SLAM_SEM_CORRECTION_FNAME, O_CREAT, 0660, 1);
    if (sem_correction == SEM_FAILED) {
        perror("sem_open/correction");
        exit(EXIT_FAILURE);
    }

    key_t keyCorr;
    // request a key
    // the key is linked to a filename, so that other programs can access it
    if (-1 != open(FILENAME_CORRECTION_SLAM, O_CREAT, 0777)) {
        keyCorr = keyCorr = ftok(FILENAME_CORRECTION_SLAM, 0);
    } else {
        perror("open");
        exit(1);
    }

    // get shared block --- create it if it doesn't exist
    int shared_correction_block_id = shmget(keyCorr, MESSAGE_BLOCK_SIZE, IPC_CREAT | SHM_R | SHM_W );

    char *result_correction;

    if (shared_correction_block_id == IPC_RESULT_ERROR) {
        result_correction = NULL;
    }

    //map the shared block int this process's memory and give me a pointer to it
    result_correction = (char*) shmat(shared_correction_block_id, NULL, 0);
    if (result_correction == (char *)IPC_RESULT_ERROR) {
        result_correction = NULL;
    }

    char *correctionFactor = "None";

    while (true) {
        sem_wait(sem_correction);
        if (strlen(result_correction) > 0) {
            correctionFactor = result_correction;
            printf("\"%s\"\n", correctionFactor);
        } else {
            printf("\"%s\"\n", correctionFactor);
        }

        sleep(1);

        sem_post(sem_correction);
    }

    sem_close(sem_correction);
    shmdt(result_correction);

    return 0;
}