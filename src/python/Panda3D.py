from subprocess import Popen, PIPE
from ARScene import *
import threading
from time import time, sleep


def get_messages(module):

    if module == "YOLO":
        p = Popen(['stdbuf', '-o0', '../cmake-build-debug/GetMessageYolo'], stdout=PIPE)
    elif module == "SLAM":
        p = Popen(['stdbuf', '-o0', '../cmake-build-debug/GetMessageSlam'], stdout=PIPE)
    elif module == "HANDS":
        p = Popen(['stdbuf', '-o0', '../cmake-build-debug/GetMessageHands'], stdout=PIPE)
    elif module == "SLAM-PLANE":
        p = Popen(['stdbuf', '-o0', '../cmake-build-debug/GetMessageSlamPlane'], stdout=PIPE)
    while True:
        result = p.stdout.readline().strip().decode()
        if module == "SLAM":
            updateSlam(result)
        elif module == "HANDS":
            updateHands(result)
        elif module == "YOLO":
            updateYOLO(result)
        elif module == "SLAM-PLANE":
            updatePlane(result)


if __name__ == "__main__":
    # creating thread
    yolo_thread = threading.Thread(target=get_messages, args=("YOLO",))
    slam_thread = threading.Thread(target=get_messages, args=("SLAM",))
    hands_thread = threading.Thread(target=get_messages, args=("HANDS",))
    slam_plane_thread = threading.Thread(target=get_messages, args=("SLAM-PLANE",))

    # starting yolo thread
    yolo_thread.start()
    # starting slam thread
    slam_thread.start()
    # starting hands thread
    hands_thread.start()
    # starting slam planes thread
    slam_plane_thread.start()

    # run panda3d instance
    pandaScene = ARScene()
    pandaScene.run()

