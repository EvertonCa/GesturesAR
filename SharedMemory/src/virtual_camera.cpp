//
// Created by Everton Cardoso on 06/10/20.
//

#include "opencv2/opencv.hpp"
#include <opencv2/core.hpp>
#include <opencv2/highgui.hpp>


int main() {
    cv::namedWindow("Test Cam", cv::WINDOW_AUTOSIZE);
    cv::VideoCapture cap(3);
    if (!cap.isOpened())
        return -1;

    cv::Mat frame;

    while (true) {

        cap >> frame;

        cv::imshow("Test Cam", frame);

        // runs until ESC key is pressed
        if (cv::waitKey(1000/30) == 27) {
            std::cout << "quit" << std::endl;
            break;
        }
    }

    return 0;
}
