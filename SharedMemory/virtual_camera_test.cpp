//
// Created by Everton Cardoso on 06/10/20.
//
#include "virtual_camera_handler.h"

int main() {
    cv::VideoCapture cap(0);
    if (!cap.isOpened())
        return -1;

    VirtualCameraHandler virtualCam1(cap, VIRTUAL_WEBCAM_1);
    VirtualCameraHandler virtualCam2(cap, VIRTUAL_WEBCAM_2);

    while (true) {

        virtualCam1.feedCam();
        virtualCam2.feedCam();

        // runs until ESC key is pressed
        if (cv::waitKey(1000/30) == 27) {
            std::cout << "quit" << std::endl;
            break;
        }
    }

    return 0;
}

