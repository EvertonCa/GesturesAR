cmake_minimum_required(VERSION 3.17)
project(SharedMemory)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_FLAGS "-std=c++11 -g -Wall -lpthread")

find_package(OpenCV REQUIRED)
include_directories(${OpenCV_INCLUDE_DIRS})

set(PROJECT_HEADERS
        includes/shared_memory.h
        includes/camera_parameters.h
        )
set(PROJECT_SOURCES
        src/shared_memory.cpp
        )

set(VIRTUAL_CAMERA_SOURCE
        includes/virtual_camera_handler.h
        )

add_executable(Destroy src/destroy_shmem.cpp ${PROJECT_SOURCES} ${PROJECT_HEADERS})
add_executable(ShareCam src/share_cam.cpp ${VIRTUAL_CAMERA_SOURCE} ${PROJECT_SOURCES} ${PROJECT_HEADERS})
add_executable(SlamGetCam src/slam_get_cam.cpp ${PROJECT_SOURCES} ${PROJECT_HEADERS})
add_executable(YoloGetCam src/yolo_get_cam.cpp ${PROJECT_SOURCES} ${PROJECT_HEADERS})

add_executable(SlamGetMessage src/slam_get_message.cpp includes/shared_memory.h src/shared_memory.cpp)
add_executable(YoloGetMessage src/yolo_get_message.cpp includes/shared_memory.h src/shared_memory.cpp)
add_executable(HandsGetMessage src/hands_get_message.cpp includes/shared_memory.h src/shared_memory.cpp)

add_executable(VirtualCamera src/virtual_camera.cpp)

target_link_libraries(ShareCam ${OpenCV_LIBS})
target_link_libraries(SlamGetCam ${OpenCV_LIBS})
target_link_libraries(YoloGetCam ${OpenCV_LIBS})
target_link_libraries(VirtualCamera ${OpenCV_LIBS})
