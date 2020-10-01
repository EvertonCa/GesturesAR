cmake_minimum_required(VERSION 3.17)
project(SharedMemory C)

set(CMAKE_C_STANDARD 99)
set(CMAKE_C_FLAGS "-g -Wall -lpthread")

add_executable(Read read_shmem.c shared_memory.h shared_memory.c)
add_executable(Write write_shmem.c shared_memory.h shared_memory.c)
add_executable(Destroy destroy_shmem.c shared_memory.h shared_memory.c)