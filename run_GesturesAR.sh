echo "~~~~~~~~~~~~~~~ Iniciando TCC - Hand Gestures ~~~~~~~~~~~~~~~"

echo "Iniciando v4l2loopback..."

#echo 0112358 | sudo -S modprobe v4l2loopback video_nr=3,4 card_label="Virtual Camera 1","Virtual Camera 2"

gnome-terminal -- bash -c 'ls && nvidia-smi; sleep 1' #open in a new terminal

#cd Thirdparty/DBoW2
#mkdir build
#cd build
#cmake .. -DCMAKE_BUILD_TYPE=Release
#make -j

#cd ../../g2o

