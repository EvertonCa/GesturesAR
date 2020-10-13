from subprocess import Popen, PIPE
import threading


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
        print(result)


if __name__ == "__main__":
    # creating thread
    yolo_thread = threading.Thread(target=get_messages, args=("YOLO",))
    slam_thread = threading.Thread(target=get_messages, args=("SLAM",))
    hands_thread = threading.Thread(target=get_messages, args=("HANDS",))

    # starting yolo thread
    yolo_thread.start()
    # starting slam thread
    slam_thread.start()
    # starting hands thread
    hands_thread.start()

    # wait until yolo thread is completely executed
    yolo_thread.join()
    # wait until slam thread is completely executed
    slam_thread.join()
    # wait until hands thread is completely executed
    hands_thread.join()
