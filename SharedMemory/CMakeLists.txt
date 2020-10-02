cmake_minimum_required(VERSION 3.17)
project(SharedMemory)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_FLAGS "-std=c++11 -g -Wall -lpthread")

find_package(OpenCV REQUIRED)
include_directories(${OpenCV_INCLUDE_DIRS})

set(PROJECT_HEADERS
        shared_memory.h
        camera_parameters.h
        )
set(PROJECT_SOURCES
        shared_memory.cpp
        )

add_executable(Destroy destroy_shmem.cpp ${PROJECT_SOURCES} ${PROJECT_HEADERS})
add_executable(ShareCam share_cam.cpp ${PROJECT_SOURCES} ${PROJECT_HEADERS})
add_executable(SlamGetCam slam_get_cam.cpp ${PROJECT_SOURCES} ${PROJECT_HEADERS})
add_executable(YoloGetCam yolo_get_cam.cpp ${PROJECT_SOURCES} ${PROJECT_HEADERS})

add_executable(SlamGetMessage slam_get_message.cpp shared_memory.h shared_memory.cpp)
add_executable(YoloGetMessage yolo_get_message.cpp shared_memory.h shared_memory.cpp)

target_link_libraries(ShareCam ${OpenCV_LIBS})
target_link_libraries(SlamGetCam ${OpenCV_LIBS})
target_link_libraries(YoloGetCam ${OpenCV_LIBS})
