//
// Created by Everton Cardoso on 25/10/20.
//

#include <algorithm>
#include <semaphore.h>
#include <fcntl.h>

#include "../includes/shared_memory.h"

int main() {
    
    sem_unlink(SLAM_SEM_PLANE_CONS_FNAME);
    sem_unlink(SLAM_SEM_PLANE_PROD_FNAME);

    sem_t *sem_slam_plane_prod = sem_open(SLAM_SEM_PLANE_PROD_FNAME, O_CREAT, 0660, 1);
    if (sem_slam_plane_prod == SEM_FAILED) {
        perror("sem_open/planeprod");
        exit(EXIT_FAILURE);
    }

    sem_t *sem_slam_plane_cons = sem_open(SLAM_SEM_PLANE_CONS_FNAME, O_CREAT, 0660, 0);
    if (sem_slam_plane_cons == SEM_FAILED) {
        perror("sem_open/planecons");
        exit(EXIT_FAILURE);
    }

    // PLANE SHARED MEMORY
    char *result_plane = attach_memory_block(FILENAME_SLAM_PLANE, MESSAGE_BLOCK_SIZE);
    if (result_plane == NULL) {
        printf("ERROR: coundn't get block\n");
        return -1;
    }

    while (true) {
        sem_wait(sem_slam_plane_cons);

        printf("%s\n", result_plane);
        result_plane[0] = 0;

        sem_post(sem_slam_plane_prod);
    }

}