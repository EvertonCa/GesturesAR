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
from crop import crop_image

#size_image = (640, 480)
size_image = (1280, 720)
#size_image = (1920, 1080)
MIN_MATCH_COUNT = 10

rating_dictionary = {
    0: "DS4",
    1: "Groot",
    2: "MiniCraque",
    3: "PS2",
    4: "Carrinho"
}


def angle_check(des, des2, namefile_list, MIN_MATCH_COUNT=10):
    matching_score = []

    for i in range(len(namefile_list)):
        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        matches = flann.knnMatch(des[i], des2, k=2)

        # store all the good matches as per Lowe's ratio test.
        good = []
        for m, n in matches:
            if m.distance < 0.7 * n.distance:
                good.append(m)
        matching_score.append(len(good))

    index_best = np.argmax(matching_score)

    if matching_score[index_best] >= MIN_MATCH_COUNT:
        print(namefile_list[index_best])
        return namefile_list[index_best]
    return None


def angle_check_multicore(i, des, des2, namefile_list, MIN_MATCH_COUNT=10):
    threshold0 = int(round(i * (len(namefile_list) + 1) / (cpu_count())))
    threshold1 = int(round((i + 1) * (len(namefile_list) + 1) / (cpu_count())))
    a = angle_check(des[threshold0:threshold1], des2[threshold0:threshold1], namefile_list[threshold0:threshold1], MIN_MATCH_COUNT)
    return a


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


def yolo2coordinates(yoloparameters_txt, imgshape):
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

    return int(ymin), int(ymax), int(xmin), int(xmax)


def save_features_database(name, photo_directory='', file_type='.jpg'):
    index = []
    namefile_list = []
    des = []
    i = 0
    for file in glob.glob(photo_directory + '*' + file_type):
        print(file)
        namefile_list.append(file)
        txtfile = file.replace(os.path.join(photo_directory[:-1], ''), os.path.join(photo_directory[:-1], 'bb', '')).replace(file_type, '.txt')
        f = open(txtfile, "r")
        boundbox_txt = f.readline()

        img_angle = cv2.imread(file, 0)
        img_angle = cv2.resize(img_angle, size_image)
        coordinates = yolo2coordinates(boundbox_txt, img_angle.shape)
        img_angle = img_angle[coordinates[0]:coordinates[1], coordinates[2]:coordinates[3]]


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
    with open(photo_directory+name + "_kp"+str(size_image), 'wb') as file_output:
        pickle.dump(index, file_output, -1)

    with open(photo_directory+name + "_des"+str(size_image), 'wb') as file_output:
        pickle.dump(des, file_output, -1)

    with open(photo_directory + name + "_list"+str(size_image), 'wb') as file_output:
        pickle.dump(namefile_list, file_output, -1)


def generate_matches_image(img1, img2, MIN_MATCH_COUNT = 10):

    # img1: queryImage
    # img2: trainImage

    # Initiate SIFT detector
    sift = cv2.SIFT_create()

    # find the keypoints and descriptors with SIFT
    kp1, des1 = sift.detectAndCompute(img1, None)
    kp2, des2 = sift.detectAndCompute(img2, None)

    FLANN_INDEX_KDTREE = 1
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
        pts = np.float32([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]]).reshape(-1, 1, 2)
        dst = cv2.perspectiveTransform(pts, M)
        polygon = np.reshape(np.int32(dst), (1, 4, 2))
        img3 = crop_image(cv2.cvtColor(img2, cv2.COLOR_GRAY2RGB), polygon)
        return img3

    print("Not enough matches are found - {}/{}".format(len(good), MIN_MATCH_COUNT))
    return None


def get_best_marker(img1, yolo):
    label = yolo[0]

    start_all_time = time.time()
    start_time = time.time()

    kp, des, namefile_list = load_features_database('sift_database', os.path.join('SIFT_database', ''))
    print("--- LOAD %s seconds ---" % (time.time() - start_time))
    start_time = time.time()

    # Initiate SIFT detector
    sift = cv2.SIFT_create()
    # find the keypoints and descriptors with SIFT
    kp2, des2 = sift.detectAndCompute(img1, None)

    # best = angle_check(des, des2, namefile_list)
    arange_cpu = np.arange(cpu_count())

    with Pool(cpu_count()) as p:
        resp = p.map(partial(angle_check_multicore, des=des[label], des2=des2, namefile_list=namefile_list[label]), arange_cpu)
    print("--- END multicore SIFT %s seconds ---" % (time.time() - start_time))
    start_time = time.time()

    l3 = []
    kp3 = []
    des3 = []
    for i in resp:
        if i is not None:
            l3.append(i)
            kp3.append(kp[label][namefile_list[label].index(i)])
            des3.append(des[label][namefile_list[label].index(i)])

    if len(l3) <= 0:
        print("Not enough matches are found")
        return None
    elif len(l3) > 1:
        best = angle_check(des3, des2, l3)
        print(best)
    else:
        best = l3[0]
        print(best)
    print("--- END SIFT %s seconds ---" % (time.time() - start_time))
    start_time = time.time()

    if best is not None:
        best_index = namefile_list[label].index(best)
        # print(best_index)
        imgbest = cv2.imread(best, cv2.IMREAD_GRAYSCALE)  # queryImage
        txtfile = namefile_list[label][best_index].replace(os.path.join(rating_dictionary[label], ''), os.path.join(
            rating_dictionary[label], 'bb', '')).replace('.jpg', '.txt')
        f = open(txtfile, "r")
        boundbox_txt = f.readline()
        coordinates = yolo2coordinates(boundbox_txt, imgbest.shape)

        imgbest = imgbest[coordinates[0]:coordinates[1], coordinates[2]:coordinates[3]]
        img3 = generate_matches_image(imgbest, img1)
        if img3 is None:
            return None
        cv2.imwrite('marcador.jpg', img3)

        print("--- marker %s seconds ---" % (time.time() - start_time))
        print("--- TUDO %s seconds ---" % (time.time() - start_all_time))

        return best
    else:
        print("Not enough matches are found")
        print("--- marker %s seconds ---" % (time.time() - start_time))
        print("--- TUDO %s seconds ---" % (time.time() - start_all_time))

    

def save_all_database():
    start_time = time.time()

    for label in rating_dictionary:
        save_features_database('sift_database', os.path.join('SIFT_database', rating_dictionary[label], ''), file_type='.jpg')
    print("--- SAVE %s seconds ---" % (time.time() - start_time))


def draw_bb(img1, img_angle):
    # Initiate SIFT detector
    sift = cv2.SIFT_create()

    # find the keypoints and descriptors with SIFT
    kp1, des1 = sift.detectAndCompute(img_angle, None)
    kp2, des2 = sift.detectAndCompute(img1, None)

    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des1, des2, k=2)

    good = []
    for m, n in matches:
        if m.distance < 0.7 * n.distance:
            good.append(m)

    if len(good) > MIN_MATCH_COUNT:
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        matchesMask = mask.ravel().tolist()
        #print(img_angle.shape)
        h, w = img_angle.shape
        pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
        #print(pts, M)
        if M is None:
            return None
        dst = cv2.perspectiveTransform(pts, M)
        img1 = cv2.polylines(img1, [np.int32(dst)], True, 255, 3, cv2.LINE_AA)
    else:
        print("Not enough matches are found - {}/{}".format(len(good), MIN_MATCH_COUNT))
        matchesMask = None

    draw_params = dict(matchColor=(0, 255, 0),  # draw matches in green color
                       singlePointColor=None,
                       matchesMask=matchesMask,  # draw only inliers
                       flags=2)
    img3 = cv2.drawMatches(img_angle, kp1, img1, kp2, good, None, **draw_params)
    # plt.imshow(cv.cvtColor(img3, cv.COLOR_BGR2RGB)),plt.show()
    plt.imshow(img3, 'gray'), plt.show()


if __name__ == '__main__':
    classe = 1
    porcentagem = 0.99
    x_esquerda = 0.
    y_superior = 854
    largura = 2276
    altura = 1439

    yolo = [classe, porcentagem, 0.23857474, 0.28224504, 0.56436956, 0.47574949]
    name_img1 = 'Groot11.jpeg'

    img1 = cv2.imread(name_img1, 0)  # imagem da webcam
    img1 = cv2.resize(img1, size_image)

    #save_all_database()

    #print(img1.shape)
    photo_directory = os.path.join('SIFT_database', rating_dictionary[classe], '')
    file_type = '.jpg'
    best_angle_name = get_best_marker(img1, yolo)
    if best_angle_name is not None:
        txtfile = best_angle_name.replace(os.path.join(photo_directory[:-1], ''),
                                          os.path.join(photo_directory[:-1], 'bb', '')).replace(file_type, '.txt')
        f = open(txtfile, "r")
        boundbox_txt = f.readline()

        img_angle = cv2.imread(best_angle_name, 0)
        img_angle = cv2.resize(img_angle, size_image)
        coordinates = yolo2coordinates(boundbox_txt, img_angle.shape)
        img_angle = img_angle[coordinates[0]:coordinates[1], coordinates[2]:coordinates[3]]

        #img1 = cv2.resize(img1, size_image)
        draw_bb(img1, img_angle)


