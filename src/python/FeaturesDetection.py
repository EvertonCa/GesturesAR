import cv2
from matplotlib import pyplot as plt
import os
import glob
import time
import numpy as np
import multiprocessing
import pickle
from multiprocessing import Process, Queue
import sys
from multiprocessing import Pool, TimeoutError, cpu_count
from functools import partial
from crop import crop_image
from threading import Thread, Lock
from subprocess import Popen, PIPE

#size_image = (640, 480)
size_image = (960, 720)
#size_image = (1200, 900)
#size_image = (1920, 1080)
MIN_MATCH_COUNT = 8

rating_dictionary = {
    0: "DS4",
    1: "Groot",
    2: "MiniCraque",
    3: "PS2",
    4: "Carrinho"
}

lock = Lock()
newer_frame = None
webcam_working = True


def get_virtual_webcam():
    global newer_frame, funciona
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    while webcam_working:
        ret, newer_frame = cap.read()

        # Display the resulting frame
        cv2.imshow('SIFT visualizer', newer_frame)
        if cv2.waitKey(1) and 0xFF == ord('q'):
            break


def start_thread_sift():
    t = Thread(target=get_virtual_webcam, daemon=True)
    t.start()


def start_marker(yolo_output):
    global webcam_working
    #cv2.imwrite("frame.jpg", newer_frame)
    img1 = newer_frame.copy()
    ans = get_best_marker(img1, yolo_output)

    if ans is not None:
        webcam_working = False
        cv2.destroyAllWindows()
        return ans
    return None


# save and load features in pickle file
def load_features_database(name, photo_directory=''):
    kp = list()
    des = list()
    namefile_list = list()

    for label in rating_dictionary:
        with open(os.path.join(photo_directory, rating_dictionary[label], name) + "_kp"+str(size_image), 'rb') as file_input:
            matrix = pickle.load(file_input)

        keypoints = []
        i = 0
        for index in matrix:
            keypoints.append([])
            for point in index:
                temp = cv2.KeyPoint(x=point[0][0], y=point[0][1], _size=point[1], _angle=point[2], _response=point[3],
                                    _octave=point[4], _class_id=point[5])
                keypoints[i].append(temp)
            i += 1
        kp.append(keypoints)

        with open(os.path.join(photo_directory, rating_dictionary[label], name) + "_des"+str(size_image), 'rb') as file_input:
            des.append(pickle.load(file_input))

        with open(os.path.join(photo_directory, rating_dictionary[label], name) + "_list"+str(size_image), 'rb') as file_input:
            namefile_list.append(pickle.load(file_input))

    return kp, des, namefile_list


def save_features_database(name, photo_directory='', file_type='.jpg'):
    index = []
    namefile_list = []
    des = []
    i = 0
    for file in glob.glob(photo_directory + '*' + file_type):
        print('calculating feature points of', file)
        namefile_list.append(file)

        img_angle = yolo2coordinates(img_name=file)
        # img_angle = cv2.imread(file, 0)
        # img_angle = cv2.resize(img_angle, size_image)


        # Initiate SIFT detector
        sift = cv2.SIFT_create()

        # find the keypoints and descriptors with SIFT
        kp1, des1 = sift.detectAndCompute(img_angle, None)
        des.append(des1)

        index.append([])

        for point in kp1:
            temp = (point.pt, point.size, point.angle, point.response, point.octave, point.class_id)
            index[i].append(temp)
        i += 1

    # Dump the keypoints and list name
    with open(photo_directory+name + "_kp" + str(size_image), 'wb') as file_output:
        pickle.dump(index, file_output, -1)

    with open(photo_directory+name + "_des" + str(size_image), 'wb') as file_output:
        pickle.dump(des, file_output, -1)

    with open(photo_directory + name + "_list" + str(size_image), 'wb') as file_output:
        pickle.dump(namefile_list, file_output, -1)


def save_all_database():
    start_time = time.time()

    for label in rating_dictionary:
        save_features_database('sift_database', os.path.join('..', '..', 'SIFT_database', rating_dictionary[label], ''),
                               file_type='.jpg')
    print("--- SAVE %s seconds ---" % (time.time() - start_time))

if not os.path.exists(os.path.join('..', '..', 'SIFT_database', 'Carrinho', 'sift_database_list' + str(size_image))):
    start_time = time.time()
    save_all_database()
    print("--- SAVE %s seconds ---" % (time.time() - start_time))

start_time = time.time()
kp, des, namefile_list = load_features_database('sift_database', os.path.join('..', '..', 'SIFT_database', ''))
print("--- LOAD %s seconds ---" % (time.time() - start_time))

# convert yolo parameters to coordinates in pixels
def yolo2coordinates(img=None, yoloparameters_txt=None, img_name=None):
    if img_name is None and yoloparameters_txt is None:
        return None

    if yoloparameters_txt is None:
        last_bar_index = img_name.rfind('/')
        if last_bar_index == -1:
            last_bar_index = img_name.rfind('\\')
        txtfile = os.path.join(img_name[:last_bar_index], 'bb', img_name[last_bar_index+1:])
        last_point_index = img_name.rfind('.')
        txtfile = txtfile.replace(img_name[last_point_index:], '.txt')

        f = open(txtfile, "r")
        yoloparameters_txt = f.readline()

    if img is None:
        img = cv2.imread(img_name, 0)
        img = cv2.resize(img, size_image)

    imgshape = img.shape

    boundbox_values = yoloparameters_txt.replace('\t', '').replace('Object Detected: ', '').replace('(center_x:','').replace('  center_y: ', '').replace('  width: ', '').replace('  height: ', '').replace(')', '').replace('\n', '').replace('%', '')
    boundbox_values = boundbox_values.split(" ")
    if len(boundbox_values) == 5:
        boundbox_values = list(map(float, boundbox_values[1:]))
    else:
        boundbox_values = list(map(float, boundbox_values[2:]))

    bx = boundbox_values[0] * imgshape[1]
    by = boundbox_values[1] * imgshape[0]
    bw = boundbox_values[2] * imgshape[1]
    bh = boundbox_values[3] * imgshape[0]

    xmin = bx - bw/2
    xmax = bx + bw/2
    ymin = by - bh/2
    ymax = by + bh/2

    if xmax > imgshape[1]:
        xmax = imgshape[1]
    if xmin < 0:
        xmin = 0
    if ymax > imgshape[0]:
        ymax = imgshape[0]
    if ymin < 0:
        ymin = 0

    answer = img[int(ymin):int(ymax), int(xmin):int(xmax)]

    return answer


def angle_check(des, des2, namefile_list, MIN_MATCH_COUNT=8):
    matching_score = []
    for i in range(len(namefile_list)):
        # BFMatcher with default params
        bf = cv2.BFMatcher()
        matches = bf.knnMatch(des[i], des2, k=2)
        # Apply ratio test
        good = []
        for m, n in matches:
            if m.distance < 0.7 * n.distance:
                good.append(m)

        print(namefile_list[i], 'tem', len(good))
        matching_score.append(len(good))

    index_best = np.argmax(matching_score)
    print(namefile_list[index_best], 'with', matching_score[index_best], 'matches')
    if matching_score[index_best] >= MIN_MATCH_COUNT:
        return namefile_list[index_best], np.amax(matching_score)
    return None


def angle_check_multicore(i, des, des2, namefile_list, MIN_MATCH_COUNT=8):
    threshold0 = int(round(i * (len(namefile_list) + 1) / (cpu_count())))
    threshold1 = int(round((i + 1) * (len(namefile_list) + 1) / (cpu_count())))
    return angle_check(des[threshold0:threshold1], des2, namefile_list[threshold0:threshold1], MIN_MATCH_COUNT)


def get_best_marker(img, yolo):
    label = int(yolo[0])

    start_all_time = time.time()
    start_time = time.time()
    # img_croped = img.copy()
    img_croped = yolo2coordinates(img, yolo)

    start_time = time.time()

    # Initiate SIFT detector
    sift = cv2.SIFT_create()
    # find the keypoints and descriptors with SIFT
    kp2, des2 = sift.detectAndCompute(img_croped, None)

    # best = angle_check(des, des2, namefile_list)
    arange_cpu = np.arange(cpu_count())

    with Pool(cpu_count()) as p:
        resp = p.map(partial(angle_check_multicore, des=des[label], des2=des2, namefile_list=namefile_list[label]), arange_cpu)
    print("--- END multicore SIFT %s seconds ---" % (time.time() - start_time))
    start_time = time.time()

    l3 = []
    kp3 = []
    des3 = []
    matches = []
    for i in resp:
        if i is not None:
            name, match = i
            l3.append(name)
            matches.append(match)
            kp3.append(kp[label][namefile_list[label].index(name)])
            des3.append(des[label][namefile_list[label].index(name)])

    if len(l3) <= 0:
        print("Not enough matches are found")
        return None
    else:
        best = l3[np.argmax(matches)]
    print("--- END SIFT %s seconds ---" % (time.time() - start_time))
    start_time = time.time()

    if best is not None:
        print("best angle in the file", best)
        imgbest = yolo2coordinates(img_name=best)
        # imgbest = cv2.imread(best, 0)
        # imgbest = cv2.resize(imgbest, size_image)

        img3 = generate_matches_image(imgbest, img)
        if img3 is None:
            return None
        cv2.imwrite('Maker.jpg', img3)

        print("--- marker %s seconds ---" % (time.time() - start_time))
        print("--- ALL %s seconds ---" % (time.time() - start_all_time))

        return best
    else:
        print("Not enough matches are found")
        print("--- ALL %s seconds ---" % (time.time() - start_all_time))


def generate_matches_image(img1, img2, MIN_MATCH_COUNT=8):
    # img1: queryImage
    # img2: trainImage

    # Initiate SIFT detector
    sift = cv2.SIFT_create()

    # find the keypoints and descriptors with SIFT
    kp1, des1 = sift.detectAndCompute(img1, None)
    kp2, des2 = sift.detectAndCompute(img2, None)

    # BFMatcher with default params
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des1, des2, k=2)
    # Apply ratio test
    good = []
    for m, n in matches:
        if m.distance < 0.7 * n.distance:
            good.append(m)

    if len(good) > MIN_MATCH_COUNT:
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        matchesMask = mask.ravel().tolist()
        h, w = img2.shape[0], img2.shape[1]
        pts = np.float32([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]]).reshape(-1, 1, 2)
        dst = cv2.perspectiveTransform(pts, M)
        polygon = np.reshape(np.int32(dst), (1, 4, 2))
        if len(img2.shape) == 2:
            img2 = cv2.cvtColor(img2, cv2.COLOR_GRAY2RGB)
        img3 = crop_image(img2, polygon)
        return img3

    print("Not enough matches are found - {}/{}".format(len(good), MIN_MATCH_COUNT))
    return None


def draw_bb(img1, img2):
    # Initiate SIFT detector
    sift = cv2.SIFT_create()

    # find the keypoints and descriptors with SIFT
    kp1, des1 = sift.detectAndCompute(img1, None)
    kp2, des2 = sift.detectAndCompute(img2, None)

    # BFMatcher with default params
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des1, des2, k=2)
    # Apply ratio test
    good = []
    for m, n in matches:
        if m.distance < 0.7 * n.distance:
            good.append(m)

    if len(good) > MIN_MATCH_COUNT:
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        matchesMask = mask.ravel().tolist()
        h, w = img2.shape
        pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)

        if M is None:
            return None
        dst = cv2.perspectiveTransform(pts, M)
        img_draw = cv2.polylines(img2, [np.int32(dst)], True, 255, 3, cv2.LINE_AA)
    else:
        print("Not enough matches are found - {}/{}".format(len(good), MIN_MATCH_COUNT))
        matchesMask = None

    draw_params = dict(matchColor=(0, 255, 0),  # draw matches in green color
                       singlePointColor=None,
                       matchesMask=matchesMask,  # draw only inliers
                       flags=2)
    img3 = cv2.drawMatches(img1, kp1, img2, kp2, good, None, **draw_params)
    # plt.imshow(cv.cvtColor(img3, cv.COLOR_BGR2RGB)),plt.show()
    plt.imshow(img3, 'gray'), plt.show()


if __name__ == '__main__':

    start_thread_sift()
    marker_angle = None

    while marker_angle is None:
        output_yolo = input()

        yolo_values = output_yolo.replace('\t', '').replace('Object Detected: ', '').replace('(center_x:',                                                                                                        '').replace(
            '  center_y: ', '').replace('  width: ', '').replace('  height: ', '').replace(')', '').replace('\n',                                                                                                            '').replace(
            '%', '')

        marker_angle = start_marker(yolo_values)
        if marker_angle is not None:
            print('Maker.jpg')
        else:
            print(None)
