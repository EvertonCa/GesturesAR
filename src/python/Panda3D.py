from subprocess import Popen, PIPE
from ARScene import *
import threading


def get_messages(module):

    if module == "YOLO":
        p = Popen(['../cmake-build-debug/GetMessageYolo'], shell=True, stdout=PIPE, stdin=PIPE)
    elif module == "SLAM":
        p = Popen(['../cmake-build-debug/GetMessageSlam'], shell=True, stdout=PIPE, stdin=PIPE)
    elif module == "HANDS":
        p = Popen(['../cmake-build-debug/GetMessageHands'], shell=True, stdout=PIPE, stdin=PIPE)
    elif module == "SLAM-PLANE":
        p = Popen(['../cmake-build-debug/GetMessageSlamPlane'], shell=True, stdout=PIPE, stdin=PIPE)
    while True:
        #value = bytes(value, 'UTF-8')  # Needed in Python 3.
        #p.stdin.write(value.encode('utf_8'))
        #p.stdin.flush()
        result = p.stdout.readline().strip().decode()
        if module == "SLAM":
            updateSlam(result)
        elif module == "HANDS":
            updateHands(result)
        elif module == "YOLO":
            updateYOLO(result)
        elif module == "SLAM-PLANE":
            print result


if __name__ == "__main__":
    # creating thread
    yolo_thread = threading.Thread(target=get_messages, args=("YOLO",))
    slam_thread = threading.Thread(target=get_messages, args=("SLAM",))
    hands_thread = threading.Thread(target=get_messages, args=("HANDS",))
    slam_plane_thread = threading.Thread(target=get_messages, args=("SLAM-PLANE",))

    #sleep(1)

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

