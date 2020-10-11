from subprocess import Popen, PIPE

if __name__ == "__main__":
    p = Popen(['../cmake-build-debug/MessagesHandler'], shell=True, stdout=PIPE, stdin=PIPE)
    while True:
        #value = bytes(value, 'UTF-8')  # Needed in Python 3.
        #p.stdin.write(value.encode('utf_8'))
        #p.stdin.flush()
        result = p.stdout.readline().strip().decode()
        print(result[:4])

        if result[:4] == "YOLO":
            continue
        elif result[:4] == "SLAM":
            continue
        else:
            continue
