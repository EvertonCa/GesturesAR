from subprocess import Popen, PIPE
from threading import Thread, Lock
from FeaturesDetection import get_best_marker
import cv2
import time
import numpy as np

lock = Lock()
frame = None


def get_messages(module):
    if module == "YOLO":
        p = Popen(['../cmake-build-debug/GetMessageYolo'], shell=True, stdout=PIPE, stdin=PIPE)
    elif module == "SLAM":
        p = Popen(['../cmake-build-debug/GetMessageSlam'], shell=True, stdout=PIPE, stdin=PIPE)
    else:
        p = Popen(['../cmake-build-debug/GetMessageHands'], shell=True, stdout=PIPE, stdin=PIPE)
    while True:
        #value = bytes(value, 'UTF-8')  # Needed in Python 3.
        #p.stdin.write(value.encode('utf_8'))
        #p.stdin.flush()
        result = p.stdout.readline().strip().decode()
        #print(result)


def get_virtual_webcam():
    global frame
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    width = 1280
    height = 720
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    while True:
        with lock:
            ret, frame = cap.read()

            # Display the resulting frame
            cv2.imshow('frame',frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break


if __name__ == "__main__":

    # creating thread
    yolo_thread = Thread(target=get_messages, args=("YOLO",))
    slam_thread = Thread(target=get_messages, args=("SLAM",))
    hands_thread = Thread(target=get_messages, args=("HANDS",))

    # starting yolo thread
    yolo_thread.start()
    # starting slam thread
    slam_thread.start()
    # starting hands thread
    hands_thread.start()

    cam_thread = Thread(target=get_virtual_webcam)
    cam_thread.start()

    time.sleep(4)
    with lock:
        print("-----" + str(frame.shape))
        cv2.imwrite('teste.png', frame)
        get_best_marker(frame, [1, 4])
