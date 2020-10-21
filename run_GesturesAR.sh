echo "~~~~~~~~~~~~~~~ Starting TCC - Hand Gestures ~~~~~~~~~~~~~~~"

echo "Starting v4l2loopback..."

echo 0112358 | sudo -S modprobe v4l2loopback video_nr=3,4 card_label="Virtual Camera 1","Virtual Camera 2"

echo "Starting Camera Sharing..."

echo "Cleaning up..."

cd SharedMemory/cmake-build-debug/

chmod +x Cleanup

./Cleanup

cd ../../

# starts the camera sharing in a new terminal
gnome-terminal -- bash -c 'cd SharedMemory/cmake-build-debug/ && echo "Sharing Camera Feed..." && chmod +x ShareCam && ./ShareCam; sleep 1'

echo "Sharing Camera Feed..."

sleep 1

# starts the listener for the messages sent by GANHands in a new terminal
gnome-terminal -- bash -c 'source SharedMemory/python/venv2/bin/activate && cd SharedMemory/python/ && echo "Listening for Messages..." && python2.7 messages_handler.py; sleep 100'

echo "Listening for Messages..."

# starts ORB-SLAM2 in a new terminal
gnome-terminal -- bash -c 'cd ORB-SLAM/ORB_SLAM2/ && echo "Starting ORB-SLAM2..." && ./Examples/Monocular/mono_tum Vocabulary/ORBvoc.txt Examples/Monocular/TUM1.yaml; sleep 1'

echo "ORB-SLAM2 started..."

# starts YOLOv4 in a new terminal
gnome-terminal -- bash -c 'cd YOLO/YOLOv4/darknet/ && echo "Starting YOLOv4..." && ./darknet detector test Complete_Database/obj.data Complete_Database/yolov4_tcc.cfg Complete_Database/weights/yolov4_tcc_final.weights; sleep 100'

echo "YOLOv4 started..."

# starts GANHands in a new terminal
gnome-terminal -- bash -c 'cd GANeratedHands/GanHandsAPI/bin/Release/ && echo "Starting GANHands..." && ./GanHands; sleep 1'

echo "GANHands started..."
