//
// Created by Everton Cardoso on 01/10/20.
//

#ifndef SHAREDMEMORY_CAMERA_PARAMETERS_H
#define SHAREDMEMORY_CAMERA_PARAMETERS_H

// ubuntu webcam = 480x640 | mac webcam = 720x1280
#define CAMERA_HEIGHT 480
#define CAMERA_WIDTH 640
#define CAMERA_CHANNELS 3
#define CAMERA_BLOCK_SIZE (CAMERA_WIDTH*CAMERA_HEIGHT*CAMERA_CHANNELS)
#define CAMERA_REFRESH_RATE 30

#define REAL_WEBCAM  "/dev/video0"
#define VIRTUAL_WEBCAM_1 "/dev/video3"
#define VIRTUAL_WEBCAM_2 "/dev/video4"

#endif //SHAREDMEMORY_CAMERA_PARAMETERS_H
