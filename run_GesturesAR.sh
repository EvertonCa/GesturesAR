echo "~~~~~~~~~~~~~~~ Starting TCC - Hand Gestures ~~~~~~~~~~~~~~~"

echo "Starting v4l2loopback..."

#echo 0112358 | sudo -S modprobe v4l2loopback video_nr=3,4 card_label="Virtual Camera 1","Virtual Camera 2"

echo "Starting Camera Sharing..."

# starts the camera sharing in a new terminal
gnome-terminal -- bash -c 'cd SharedMemory/cmake-build-debug/ && echo "Sharing Camera Feed..." && chmod +x ShareCam && ./ShareCam; sleep 1'

echo "Sharing Camera Feed..."

# starts the listener for the messages sent by GANHands in a new terminal
gnome-terminal -- bash -c 'cd SharedMemory/cmake-build-debug/ && echo "Listening to GANHands..." && chmod +x HandsGetMessage && ./HandsGetMessage; sleep 1'

echo "Listening to GANHands..."

# starts the listener for the messages sent by YOLO in a new terminal
gnome-terminal -- bash -c 'cd SharedMemory/cmake-build-debug/ && echo "Listening to YOLO..." && chmod +x YoloGetMessage && ./YoloGetMessage; sleep 1'

echo "Listening to YOLO..."

# starts the listener for the messages sent by ORB-SLAM2 in a new terminal
gnome-terminal -- bash -c 'cd SharedMemory/cmake-build-debug/ && echo "Listening to ORB-SLAM2..." && chmod +x SlamGetMessage && ./SlamGetMessage; sleep 1'

echo "Listening to ORB-SLAM2..."

# starts ORB-SLAM2 in a new terminal
gnome-terminal -- bash -c 'cd ORB-SLAM/ORB_SLAM2/ && echo "Starting ORB-SLAM2..." && ./Examples/Monocular/mono_tum Vocabulary/ORBvoc.txt Examples/Monocular/TUM1.yaml; sleep 1'

echo "Starting ORB-SLAM2..."

# starts YOLOv4 in a new terminal
gnome-terminal -- bash -c 'cd YOLO/YOLOv4/darknet/ && echo "Starting YOLOv4..." && ./darknet detector test Complete_Database/obj.data Complete_Database/yolov4_tcc.cfg Complete_Database/weights/yolov4_tcc_final.weights; sleep 100'

echo "Starting YOLOv4..."

# starts GANHands in a new terminal
gnome-terminal -- bash -c 'cd GANeratedHands/GanHandsAPI/bin/Release/ && echo "Starting GANHands..." && ./GanHands; sleep 1'

echo "Starting GANHands..."

#cd Thirdparty/DBoW2
#mkdir build
#cd build
#cmake .. -DCMAKE_BUILD_TYPE=Release
#make -j

#cd ../../g2o

