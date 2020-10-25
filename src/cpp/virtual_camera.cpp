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
    cv::VideoCapture cap(91);

    if (!cap.isOpened())
        return -1;

    cv::Mat frame;
    int i = 0;

    while (true) {

        cap >> frame;

        std::cout << frame.size << std::endl;

        cv::imshow("Test Cam", frame);

        // runs until ESC key is pressed
        if (cv::waitKey(1000/30) == 27) {
            cv::imwrite("frame" + std::to_string(i)+ ".jpg", frame);
            i++;
        }
    }

    return 0;
}
