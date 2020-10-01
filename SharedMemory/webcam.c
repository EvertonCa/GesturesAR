//
// Created by Everton Cardoso on 01/10/20.
//
#include "cv.h"
#include "highgui.h"
int main(int argc, char** argv)
{
    CvCapture* capture=0;
    IplImage* frame=0;
    capture = cvCaptureFromAVI("C:\\video.avi");
    if( !capture )
        throw "Error when reading steam_avi";

    cvNamedWindow( "w", 1);

    for( ; ; )
    {
        frame = cvQueryFrame( capture );
        if(!frame)
            break;
        cvShowImage("w", frame);
    }
    cvWaitKey(0);
    cvDestroyWindow("w");
    cvReleaseImage(&frame);
}

