//
// Created by Everton Cardoso on 06/10/20.
//

#ifndef SHAREDMEMORY_VIRTUAL_CAMERA_HANDLER_H
#define SHAREDMEMORY_VIRTUAL_CAMERA_HANDLER_H

#include <opencv2/opencv.hpp>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/videodev2.h>

class VirtualCameraHandler {
    cv::VideoCapture cam;
    int output;
    struct v4l2_format vid_format;
    size_t framesize;

    bool setup();

public:
    VirtualCameraHandler(cv::VideoCapture cap);

    bool feedCam();
};

#endif //SHAREDMEMORY_VIRTUAL_CAMERA_HANDLER_H
