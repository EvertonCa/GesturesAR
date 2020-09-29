import numpy as np
import cv2
from matplotlib import pyplot as plt
import os
import pathlib
import glob
import time
import numpy as np
import multiprocessing
import pickle
from multiprocessing import Process, Queue
import sys
from multiprocessing import Pool, TimeoutError, cpu_count
from functools import partial

size_image = (int(320/2), int(180/2))
#size_image = (1920, 1080)
MIN_MATCH_COUNT = 10


def angle_check(des, des2, namefile_list, MIN_MATCH_COUNT=10):
    matching_score = []

    for i in range(len(namefile_list)):
        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        matches = flann.knnMatch(des[i], des2, k=2)

        good = []
        for m, n in matches:
            if m.distance < 0.7 * n.distance:
                good.append(m)
        matching_score.append(len(good))

    index_best = np.argmax(matching_score)

    if matching_score[index_best] > MIN_MATCH_COUNT:
        print(namefile_list[index_best])
        return namefile_list[index_best]
    print(None)
    return None


def angle_check_multicore(i, des, des2, namefile_list, MIN_MATCH_COUNT=10):
    threshold0 = int(round(i * (len(namefile_list) + 1) / (cpu_count())))
    threshold1 = int(round((i + 1) * (len(namefile_list) + 1) / (cpu_count())))
    a = angle_check(des[threshold0:threshold1], des2[threshold0:threshold1], namefile_list[threshold0:threshold1], MIN_MATCH_COUNT)
    return a


def get_transformation_matrix(kp1, des1, kp2, des2):

    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des1, des2, k=2)

    good = []
    for m, n in matches:
        if m.distance < 0.7 * n.distance:
            good.append(m)

    src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

    M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

    return M, mask


def load_features_database(name, photo_directory=''):
    with open(photo_directory + name + "_kp", 'rb') as file_input:
        matrix = pickle.load(file_input)

    kp = []
    i = 0
    for index in matrix:
        kp.append([])
        for point in index:
            temp = cv2.KeyPoint(x=point[0][0], y=point[0][1], _size=point[1], _angle=point[2], _response=point[3],
                                _octave=point[4], _class_id=point[5])
            kp[i].append(temp)
        i += 1

    with open(photo_directory + name + "_des", 'rb') as file_input:
        des = pickle.load(file_input)

    with open(photo_directory + name + "_list", 'rb') as file_input:
        namefile_list = pickle.load(file_input)

    return kp, des, namefile_list


def save_features_database(name, photo_directory='', file_type='.JPG'):
    index = []
    namefile_list = []
    des = []
    i = 0
    for file in glob.glob(photo_directory + '*' + file_type):
        print(file)
        namefile_list.append(file)

        # txtfile = file.replace(photo_directory, 'labels/').replace(file_type, '.txt')
        # f = open(txtfile, "r")
        # boundbox_values = f.readline().replace('\n', '')
        # boundbox_values = boundbox_values.split(" ")
        # boundbox_values = list(map(float, boundbox_values[1:]))

        img_angle = cv2.imread(file, 0)
        #img_angle = img_angle.crop[boundbox_values[0]:boundbox_values[1], boundbox_values[2]:boundbox_values[3]]

        # Initiate SIFT detector
        sift = cv2.SIFT_create()

        # find the keypoints and descriptors with SIFT
        kp1, des1 = sift.detectAndCompute(img_angle, None)
        #db.kp.append(kp1)
        #des.append(des1)
        des.append(des1)

        index.append([])

        for point in kp1:
            temp = (point.pt, point.size, point.angle, point.response, point.octave, point.class_id)
            index[i].append(temp)
        i += 1

    # Dump the keypoints and list name
    with open(photo_directory+name + "_kp", 'wb') as file_output:
        pickle.dump(index, file_output, -1)

    with open(photo_directory+name + "_des", 'wb') as file_output:
        pickle.dump(des, file_output, -1)

    with open(photo_directory + name + "_list", 'wb') as file_output:
        pickle.dump(namefile_list, file_output, -1)


def generate_matches_image(name_img1, name_img2):
    MIN_MATCH_COUNT = 10

    img1 = cv2.imread(name_img1, 0)  # queryImage
    img2 = cv2.imread(name_img2, 0)  # trainImage

    # Initiate SIFT detector
    sift = cv2.SIFT()

    # find the keypoints and descriptors with SIFT
    kp1, des1 = sift.detectAndCompute(img1, None)
    kp2, des2 = sift.detectAndCompute(img2, None)

    FLANN_INDEX_KDTREE = 0
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)

    flann = cv2.FlannBasedMatcher(index_params, search_params)

    matches = flann.knnMatch(des1, des2, k=2)

    # store all the good matches as per Lowe's ratio test.
    good = []
    for m, n in matches:
        if m.distance < 0.7 * n.distance:
            good.append(m)

    if len(good) > MIN_MATCH_COUNT:
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        matchesMask = mask.ravel().tolist()

        h, w = img1.shape
        pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
        dst = cv2.perspectiveTransform(pts, M)

        img2 = cv2.polylines(img2, [np.int32(dst)], True, 255, 3, cv2.LINE_AA)

    else:
        print("Not enough matches are found - %d/%d" % (len(good), MIN_MATCH_COUNT))
        matchesMask = None

    draw_params = dict(matchColor=(0, 255, 0),  # draw matches in green color
                       singlePointColor=None,
                       matchesMask=matchesMask,  # draw only inliers
                       flags=2)

    img3 = cv2.drawMatches(img1, kp1, img2, kp2, good, None, **draw_params)

    plt.imshow(img3, 'gray'), plt.show()


if __name__ == '__main__':
    label = 0# label do yolo
    name_img1 = 'Capturar.jpg'
    img1 = cv2.imread(name_img1, 0)  # imagem da webcam

    #img1 = cv2.resize(img1, size_image)
    rating_dictionary = {
        0: "DS4",
        1: "ImGroot",
        2: "MiniCraque",
        3: "PS2",
        4: "Carro"
    }

    start_time = time.time()

    #save_features_database('sift_database', rating_dictionary[label] + '/', file_type='.JPG')
    kp, des, namefile_list = load_features_database('sift_database', rating_dictionary[label] + '/')

    # Initiate SIFT detector
    sift = cv2.SIFT_create()
    # find the keypoints and descriptors with SIFT
    kp2, des2 = sift.detectAndCompute(img1, None)

    #best = angle_check(des, des2, namefile_list)
    arange_cpu = np.arange(cpu_count())

    with Pool(cpu_count()) as p:
        resp = p.map(partial(angle_check_multicore, des=des, des2=des2, namefile_list=namefile_list), arange_cpu)
    print(resp)
    l3 = []
    kp3 = []
    des3 = []
    for i in resp:
        if i is not None:
            l3.append(i)
            kp3.append(kp[namefile_list.index(i)])
            des3.append(des[namefile_list.index(i)])
    print(l3)

    if len(l3) == 0:
        print("Not enough matches are found")
        sys.exit()
    elif len(l3) > 1:
        best = angle_check(des3, des2, l3)
        print(best)
    else:
        best = l3[0]
        print(best)
    print("--- %s seconds ---" % (time.time() - start_time))

    if best is not None:
        best_index = namefile_list.index(best)
        M, mask = get_transformation_matrix(kp[best_index], des[best_index], kp2, des2)
        generate_matches_image(name_img1, best)
    else:
        print("Not enough matches are found")



    #file_name = 'DS4/PlayStation2_1.JPG'
    #print(file_name)
