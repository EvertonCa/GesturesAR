//
// Created by Everton Cardoso on 01/10/20.
//

#include "opencv2/opencv.hpp"

int main(int, char**) {
    cv::namedWindow("Video", cv::WINDOW_AUTOSIZE);
    cv::VideoCapture cap(0);
    if (!cap.isOpened())
        return -1;

    cv::Mat frame;
    for ( ; ; ) {
        cap >> frame;
        cv::imshow("Video", frame);
        if (cv::waitKey(33) >= 0) break;
    }
    return 0;
}