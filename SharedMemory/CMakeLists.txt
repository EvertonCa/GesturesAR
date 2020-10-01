cmake_minimum_required(VERSION 3.17)
project(SharedMemoryC__)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_FLAGS "-std=c++11 -g -Wall -lpthread")

find_package(OpenCV REQUIRED)
include_directories(${OpenCV_INCLUDE_DIRS})

set(PROJECT_HEADERS
        shared_memory.h
        )
set(PROJECT_SOURCES
        shared_memory.cpp
        )

add_executable(Read read_shmem.cpp ${PROJECT_SOURCES} ${PROJECT_HEADERS})
add_executable(Write write_shmem.cpp ${PROJECT_SOURCES} ${PROJECT_HEADERS})
add_executable(Destroy destroy_shmem.cpp ${PROJECT_SOURCES} ${PROJECT_HEADERS} destroy_shmem.cpp)
add_executable(Webcam webcam.cpp)

target_link_libraries(Webcam ${OpenCV_LIBS})
