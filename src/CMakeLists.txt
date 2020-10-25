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
        cpp/shared_memory.cpp
        )

set(VIRTUAL_CAMERA_SOURCE
        includes/virtual_camera_handler.h
        )

add_executable(Cleanup cpp/destroy_shmem.cpp ${PROJECT_SOURCES} ${PROJECT_HEADERS})
add_executable(ShareCam cpp/share_cam.cpp ${VIRTUAL_CAMERA_SOURCE} ${PROJECT_SOURCES} ${PROJECT_HEADERS})

add_executable(GetMessageYolo cpp/get_message_yolo.cpp includes/shared_memory.h cpp/shared_memory.cpp)
add_executable(GetMessageSlam cpp/get_message_slam.cpp includes/shared_memory.h cpp/shared_memory.cpp)
add_executable(GetMessageHands cpp/get_message_hands.cpp includes/shared_memory.h cpp/shared_memory.cpp)

add_executable(TesterReceiver cpp/tester_receiver.cpp )
add_executable(YoloCorrectionSender cpp/yolo_correction_sender.cpp)

add_executable(VirtualCamera cpp/virtual_camera.cpp)

add_executable(OpenCVCalibrator cpp/opencv_calibrator.cpp)


target_link_libraries(ShareCam ${OpenCV_LIBS})
target_link_libraries(VirtualCamera ${OpenCV_LIBS})
target_link_libraries(OpenCVCalibrator ${OpenCV_LIBS})
