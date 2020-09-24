import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
import os
import pathlib
import glob
import time
import numpy as np


size_image = (int(320/2), int(180/2))
#size_image = (1920, 1080)
MIN_MATCH_COUNT = 10

def angle_check(img, photo_directory, MIN_MATCH_COUNT=10):

    files_name = []
    matching_score = []
    for file in glob.glob(photo_directory + "*.JPG"):
        print(file)
        files_name.append(file)

        #txtfile = file.replace(photo_directory, 'labels/').replace('.JPG', '.txt')
        #f = open(txtfile, "r")
        #boundbox_values = f.readline().replace('\n', '')
        #boundbox_values = boundbox_values.split(" ")
        #boundbox_values = list(map(float, boundbox_values[1:]))

        img1 = cv.imread(file, 0)
        #img1 = img1.crop[boundbox_values[0]:boundbox_values[1], boundbox_values[2]:boundbox_values[3]]
        #img1 = cv.resize(img1, size_image)

        # Initiate SIFT detector
        sift = cv.SIFT_create()

        # find the keypoints and descriptors with SIFT
        kp1, des1 = sift.detectAndCompute(img, None)
        kp2, des2 = sift.detectAndCompute(img1, None)

        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)
        flann = cv.FlannBasedMatcher(index_params, search_params)
        matches = flann.knnMatch(des1, des2, k=2)

        good = []
        for m, n in matches:
            if m.distance < 0.7 * n.distance:
                good.append(m)
        matching_score.append(len(good))
        #print(len(good))
    index_best = np.argmax(matching_score)
    return files_name[index_best]
'''''

# store all the good matches as per Lowe's ratio test.
good = []
for m, n in matches:
    if m.distance < 0.7*n.distance:
        good.append(m)

if len(good) > MIN_MATCH_COUNT:
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    M, mask = cv.findHomography(src_pts, dst_pts, cv.RANSAC, 5.0)
    matchesMask = mask.ravel().tolist()
    print(img1.shape)
    h, w = img1.shape
    pts = np.float32([[0, 0], [0, h-1], [w-1, h-1], [w-1, 0]]).reshape(-1, 1, 2)
    dst = cv.perspectiveTransform(pts, M)
    img2 = cv.polylines(img2, [np.int32(dst)], True, 255, 3, cv.LINE_AA)
else:
    print("Not enough matches are found - {}/{}".format(len(good), MIN_MATCH_COUNT))
    matchesMask = None

draw_params = dict(matchColor=(0, 255, 0),  # draw matches in green color
                   singlePointColor=None,
                   matchesMask=matchesMask,  # draw only inliers
                   flags=2)
img3 = cv.drawMatches(img1, kp1, img2, kp2, good, None, **draw_params)
#plt.imshow(cv.cvtColor(img3, cv.COLOR_BGR2RGB)),plt.show()
plt.imshow(img3, 'gray'), plt.show()
'''''

if __name__ == '__main__':
    label = 0# label do yolo
    img1 = cv.imread('Capturar.jpg', 0)  # imagem da webcam
    #img1 = cv.resize(img1, size_image)
    rating_dictionary = {
        0: "DS4",
        1: "ImGroot",
        2: "MiniCraque",
        3: "PS2",
        4: "Carro"
    }
    start_time = time.time()
    file_name = angle_check(img1, rating_dictionary[label] + '/')
    #file_name = 'DS4/PlayStation2_1.JPG'
    print(file_name)

    img2 = cv.imread(file_name, 0)
    #img2 = cv.resize(img2, size_image)
    # Initiate SIFT detector
    sift = cv.SIFT_create()

    # find the keypoints and descriptors with SIFT
    kp1, des1 = sift.detectAndCompute(img1, None)
    kp2, des2 = sift.detectAndCompute(img2, None)

    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)
    flann = cv.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des1, des2, k=2)

    good = []
    for m, n in matches:
        if m.distance < 0.7 * n.distance:
            good.append(m)

    if len(good) > MIN_MATCH_COUNT:
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
        M, mask = cv.findHomography(src_pts, dst_pts, cv.RANSAC, 5.0)
        matchesMask = mask.ravel().tolist()
        print(img1.shape)
        h, w = img1.shape
        pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
        dst = cv.perspectiveTransform(pts, M)
        img2 = cv.polylines(img2, [np.int32(dst)], True, 255, 3, cv.LINE_AA)
    else:
        print("Not enough matches are found - {}/{}".format(len(good), MIN_MATCH_COUNT))
        matchesMask = None

    draw_params = dict(matchColor=(0, 255, 0),  # draw matches in green color
                       singlePointColor=None,
                       matchesMask=matchesMask,  # draw only inliers
                       flags=2)
    img3 = cv.drawMatches(img1, kp1, img2, kp2, good, None, **draw_params)
    #plt.imshow(cv.cvtColor(img3, cv.COLOR_BGR2RGB)),plt.show()
    plt.imshow(img3, 'gray'), plt.show()

    print("--- %s seconds ---" % (time.time() - start_time))
