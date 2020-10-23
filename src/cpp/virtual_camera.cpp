//
// Created by Everton Cardoso on 06/10/20.
//

#include "opencv2/opencv.hpp"
#include <opencv2/core.hpp>
#include <opencv2/highgui.hpp>
#include <iostream>
#include <string>

int main() {
    cv::namedWindow("Test Cam", cv::WINDOW_AUTOSIZE);
    cv::VideoCapture cap(0);
    cap.set(CV_CAP_PROP_FOURCC, CV_FOURCC('M', 'J', 'P', 'G'));
    cap.set(CV_CAP_PROP_FRAME_WIDTH, 1280);
    cap.set(CV_CAP_PROP_FRAME_HEIGHT, 720);
    cap.set(CV_CAP_PROP_AUTOFOCUS, 0);

    if (!cap.isOpened())
        return -1;

    cv::Mat frame;
    int i = 0;

    while (true) {

        cap >> frame;

        cv::imshow("Test Cam", frame);

        // runs until ESC key is pressed
        if (cv::waitKey(1000/30) == 27) {
            cv::imwrite("frame" + std::to_string(i)+ ".jpg", frame);
            i++;
        }
    }

    return 0;
}
