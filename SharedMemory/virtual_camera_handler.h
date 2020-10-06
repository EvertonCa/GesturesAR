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

#include "camera_parameters.h"

class VirtualCameraHandler {
public:
    VirtualCameraHandler(cv::VideoCapture cap) {
        cam = cap;
        setup();
    }

    bool feedCam() {
        // grab frame
        cv::Mat frame;
        if (not cam.grab()) {
            std::cerr << "ERROR: could not read from camera!\n";
            return false;
        }
        cam.retrieve(frame);

        cv::Mat result;
        cv::cvtColor(frame, result, cv::COLOR_BGR2RGB);

        // write frame to output device
        size_t written = write(output, result.data, framesize);
        if (written < 0) {
            std::cerr << "ERROR: could not write to output device!\n";
            close(output);
            return false;
        }
    }
private:
    cv::VideoCapture cam;
    int output;
    struct v4l2_format vid_format;
    size_t framesize;

    bool setup() {

        if (not cam.isOpened()) {
            std::cerr << "ERROR: could not open camera!\n";
            return -1;
        }
        cam.set(cv::CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH);
        cam.set(cv::CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT);

        // open output device
        output = open(VIRTUAL_WEBCAM_1, O_RDWR);
        if(output < 0) {
            std::cerr << "ERROR: could not open output device!\n" <<
                      strerror(errno); return -2;
        }

        // configure params for output device
        memset(&vid_format, 0, sizeof(vid_format));
        vid_format.type = V4L2_BUF_TYPE_VIDEO_OUTPUT;

        if (ioctl(output, VIDIOC_G_FMT, &vid_format) < 0) {
            std::cerr << "ERROR: unable to get video format!\n" <<
                      strerror(errno); return -1;
        }

        framesize = CAMERA_BLOCK_SIZE;
        vid_format.fmt.pix.width = cam.get(cv::CAP_PROP_FRAME_WIDTH);
        vid_format.fmt.pix.height = cam.get(cv::CAP_PROP_FRAME_HEIGHT);

        // NOTE: change this according to below filters...
        // Chose one from the supported formats on Chrome:
        // - V4L2_PIX_FMT_YUV420,
        // - V4L2_PIX_FMT_Y16,
        // - V4L2_PIX_FMT_Z16,
        // - V4L2_PIX_FMT_INVZ,
        // - V4L2_PIX_FMT_YUYV,
        // - V4L2_PIX_FMT_RGB24,
        // - V4L2_PIX_FMT_MJPEG,
        // - V4L2_PIX_FMT_JPEG
        vid_format.fmt.pix.pixelformat = V4L2_PIX_FMT_RGB24;

        vid_format.fmt.pix.sizeimage = framesize;
        vid_format.fmt.pix.field = V4L2_FIELD_NONE;

        if (ioctl(output, VIDIOC_S_FMT, &vid_format) < 0) {
            std::cerr << "ERROR: unable to set video format!\n" <<
                      strerror(errno); return -1;
        }
    }
};

#endif //SHAREDMEMORY_VIRTUAL_CAMERA_HANDLER_H
