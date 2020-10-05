// Kara.cpp : Defines the entry point for the console application.
//

#include "Kara.hpp"

#include "opencv2/opencv.hpp"
#include <opencv2/core.hpp>
#include <opencv2/highgui.hpp>

bool run() {
	Kara kara;

	cv::namedWindow("GANHands Cam", cv::WINDOW_AUTOSIZE);
    cv::VideoCapture cap(0);
    if (!cap.isOpened())
        return -1;

    cv::Mat frame;

    int frame_cont = 0;

    bool whileContinue = true;

	while(whileContinue)
	{

		cap >> frame;

		kara.processImg(frame);
		//toPanda = kara.getCurrent3D();
		std::cout << "3D: " << kara.getCurrent3D() << std::endl;
		//std::cout << "2D: " << kara.getCurrent2D() << std::endl;
			

		frame_cont ++;

		int waitKeyPressed = cv::waitKey(1000/30);

		if ( waitKeyPressed >= 0) {
			if (waitKeyPressed == 27) { // if "ESQ" is pressed, the program ends.
        		whileContinue = false;
			} else if (waitKeyPressed == 82 || waitKeyPressed == 114){ // if "R" is pressed, resets the bb and the skeleton (will not reset 3D)
				kara.resetSkeleton();
				//kara.rescaleSkeleton();
				kara.resetBoundingBox();
			} else if (waitKeyPressed == 66 || waitKeyPressed == 98){ // if "B" is pressed, everything will be reseted.
				return false;
			}
    	}
		
    }

    kara.save_joint_positions();
	kara.save_raw_joint_positions();
	kara.save_fingertip_positions();
	kara.save_Bboxes_positions();

	return true;
}


int main()
{
	while(!run());
		
	return 0;
}

