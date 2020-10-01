//
// Created by Everton Cardoso on 01/10/20.
//

#ifndef SHAREDMEMORY_CAMERA_PARAMETERS_H
#define SHAREDMEMORY_CAMERA_PARAMETERS_H

// ubuntu webcam = 480x640 | mac webcam = 720x1280
#define HEIGHT 720
#define WIDTH 1280
#define CHANNELS 3
#define BLOCK_SIZE (WIDTH*HEIGHT*CHANNELS)
#define REFRESH_RATE 30

#endif //SHAREDMEMORY_CAMERA_PARAMETERS_H
