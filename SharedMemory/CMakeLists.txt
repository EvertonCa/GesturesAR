cmake_minimum_required(VERSION 3.17)
project(SharedMemory C)

set(CMAKE_C_STANDARD 99)
set(CMAKE_C_FLAGS "-g -Wall -lpthread")

set(PROJECT_HEADERS
        shared_memory.h
        )
set(PROJECT_SOURCES
        shared_memory.c
        )

add_executable(Read read_shmem.c ${PROJECT_SOURCES} ${PROJECT_HEADERS})
add_executable(Write write_shmem.c ${PROJECT_SOURCES} ${PROJECT_HEADERS})
add_executable(Destroy destroy_shmem.c ${PROJECT_SOURCES} ${PROJECT_HEADERS})
add_executable(Webcam webcam.c)