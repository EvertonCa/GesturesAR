import cv2
from matplotlib import pyplot as plt
import os
import glob
import time
import numpy as np
import pickle
from multiprocessing import Pool
from multiprocessing import cpu_count
from functools import partial
from crop import crop_image
from threading import Thread, Lock
from shutil import copyfile


def angle_check(des, des2, namefile_list):
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

        matching_score.append(len(good))

    index_best = np.argmax(matching_score)
    if matching_score[index_best] >= FeaturesDetection((640, 480)).MIN_MATCH_COUNT:
        return namefile_list[index_best]
    return None


def angle_check_multicore(i, des, des2, namefile_list):
    threshold0 = int(round(i * (len(namefile_list) + 1) / (cpu_count())))
    threshold1 = int(round((i + 1) * (len(namefile_list) + 1) / (cpu_count())))
    return angle_check(des[threshold0:threshold1], des2, namefile_list[threshold0:threshold1])


class FeaturesDetection:
    def __init__(self, size_image):
        self.size_image = size_image

        self.MIN_MATCH_COUNT = 8

        self.rating_dictionary = {
            0: "DS4",
            1: "Groot",
            2: "MiniCraque",
            3: "PS2",
            4: "Carrinho"
        }
        self.label_yolo = {
            'Dualshock4': 0,
            'IamGroot': 1,
            'MiniCraque': 2,
            'PlayStation2': 3,
            'Carrinho': 4
        }

        self.newer_frame = None
        self.webcam_working = True

        if not os.path.exists(
                os.path.join('SIFT_database', 'Carrinho', 'sift_database_list' + str(self.size_image))):
            # start_time = time.time()
            self.save_all_database()

        # start_time = time.time()
        self.des, self.namefile_list = self.load_features_database('sift_database',
                                                                            os.path.join('SIFT_database', ''))

    def get_virtual_webcam(self):
        cap = cv2.VideoCapture(3)
        ret, self.newer_frame = cap.read()

    def start_thread_webcam(self):
        t = Thread(target=self.get_virtual_webcam)
        t.start()

    def start_marker(self, yolo_output):
        self.get_virtual_webcam()
        cv2.imwrite("frame.jpg", self.newer_frame)
        img1 = self.newer_frame.copy()

        ans = self.get_best_marker(img1, yolo_output)

        if ans is not None:
            self.webcam_working = False
            cv2.destroyAllWindows()
            return 'Maker.jpg'
        return None

    # save and load features in pickle file
    def load_features_database(self, name, photo_directory=''):
        des = list()
        namefile_list = list()

        for label in self.rating_dictionary:

            with open(
                    os.path.join(photo_directory, self.rating_dictionary[label], name) + "_des" + str(self.size_image),
                    'rb') as file_input:
                des.append(pickle.load(file_input))

            with open(
                    os.path.join(photo_directory, self.rating_dictionary[label], name) + "_list" + str(self.size_image),
                    'rb') as file_input:
                namefile_list.append(pickle.load(file_input))

        return des, namefile_list

    def save_features_database(self, name, photo_directory='', file_type='.jpg'):
        namefile_list = []
        des = []
        i = 0
        for file in glob.glob(photo_directory + '*' + file_type):
            # print('calculating feature points of', file)
            namefile_list.append(file)

            img_angle = self.yolo2coordinates(img_name=file)

            # Initiate SIFT detector
            sift = cv2.xfeatures2d.SIFT_create()

            # find the keypoints and descriptors with SIFT
            kp1, des1 = sift.detectAndCompute(img_angle, None)
            des.append(des1)


        with open(photo_directory + name + "_des" + str(self.size_image), 'wb') as file_output:
            pickle.dump(des, file_output, -1)

        with open(photo_directory + name + "_list" + str(self.size_image), 'wb') as file_output:
            pickle.dump(namefile_list, file_output, -1)

    def save_all_database(self):
        start_time = time.time()

        for label in self.rating_dictionary:
            self.save_features_database('sift_database',
                                        os.path.join('SIFT_database', self.rating_dictionary[label], ''),
                                        file_type='.jpg')

    # convert yolo parameters to coordinates in pixels
    def yolo2coordinates(self, img=None, yoloparameters_txt=None, img_name=None):
        if img_name is None and yoloparameters_txt is None:
            return None

        if yoloparameters_txt is None:
            last_bar_index = img_name.rfind('/')
            if last_bar_index == -1:
                last_bar_index = img_name.rfind('\\')
            txtfile = os.path.join(img_name[:last_bar_index], 'bb', img_name[last_bar_index + 1:])
            last_point_index = img_name.rfind('.')
            txtfile = txtfile.replace(img_name[last_point_index:], '.txt')

            f = open(txtfile, "r")
            yoloparameters_txt = f.readline()

        if img is None:
            img = cv2.imread(img_name, 0)
            img = cv2.resize(img, self.size_image)

        imgshape = img.shape

        boundbox_values = yoloparameters_txt.replace('\t', '').replace('Object Detected: ', '').replace('(center_x:',
                                                                                                        '').replace(
            '  center_y: ', '').replace('  width: ', '').replace('  height: ', '').replace(')', '').replace('\n',
                                                                                                            '').replace(
            '%', '')
        boundbox_values = boundbox_values.split(" ")
        if len(boundbox_values) == 5:
            boundbox_values = list(map(float, boundbox_values[1:]))
        else:
            boundbox_values = list(map(float, boundbox_values[2:]))

        bx = boundbox_values[0] * imgshape[1]
        by = boundbox_values[1] * imgshape[0]
        bw = boundbox_values[2] * imgshape[1]
        bh = boundbox_values[3] * imgshape[0]

        xmin = bx - bw / 2
        xmax = bx + bw / 2
        ymin = by - bh / 2
        ymax = by + bh / 2

        if xmax > imgshape[1]:
            xmax = imgshape[1]
        if xmin < 0:
            xmin = 0
        if ymax > imgshape[0]:
            ymax = imgshape[0]
        if ymin < 0:
            ymin = 0

        return img[int(ymin):int(ymax), int(xmin):int(xmax)]

    def get_best_marker(self, img, yolo):
        yolo = yolo.replace('\t', '').replace('Object Detected: ', '').replace('(center_x:', '').replace(
            '  center_y: ', '').replace('  width: ', '').replace('  height: ', '').replace(')', '').replace('\n',
                                                                                                            '').replace(
            '%', '').replace(':', '')

        label_name = yolo.split(' ')[0]

        label = int(yolo[0])

        img_croped = self.yolo2coordinates(img, yolo)

        start_time = time.time()

        # Initiate SIFT detector
        sift = cv2.xfeatures2d.SIFT_create()

        # find the keypoints and descriptors with SIFT
        kp2, des2 = sift.detectAndCompute(img_croped, None)

        best = angle_check(des=self.des[label], des2=des2, namefile_list=self.namefile_list[label])

        # print best
        kp2, des2 = None, None
        return best

    def generate_matches_image(self, img1, img2):
        # Initiate SIFT detector
        sift = cv2.xfeatures2d.SIFT_create()

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

        if len(good) > self.MIN_MATCH_COUNT:
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

            img_ans = crop_image(img2, polygon)

            # draw perspective matching in image
            pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
            dst = cv2.perspectiveTransform(pts, M)
            img_draw = cv2.polylines(img2, [np.int32(dst)], True, 255, 3, cv2.LINE_AA)

            draw_params = dict(matchColor=(0, 255, 0),  # draw matches in green color
                               singlePointColor=None,
                               matchesMask=matchesMask,  # draw only inliers
                               flags=2)
            img3 = cv2.drawMatches(img1, kp1, img_draw, kp2, good, None, **draw_params)
            cv2.imwrite('SIFT matching points.png', img3)

            return img_ans

        return None


if __name__ == '__main__':
    objetos = {1: 'Carrinho',
               2: 'DS4',
               3: 'Groot',
               4: 'MiniCraque',
               5: 'PS2'}

    resolutions = [(640, 480), (800, 600), (960, 720), (1024, 768), (1152, 864), (1280, 960), (1400, 1050),
                   (1440, 1080), (1600, 1200), (1856, 1392), (1920, 1440), (2048, 1536)]

    start_time = time.time()
    vaitravar = True

    for resolution in resolutions:
        print resolution

        deteccao = FeaturesDetection(resolution)
        acertos = np.zeros(5)
        erros = np.zeros(5)

        for object_index in objetos:
            directory = os.path.join('YOLO train', objetos[object_index], 'images', '')
            entries = os.listdir(directory)
            directory_bb = directory.replace('images', 'labels')

            for file in entries:
                if vaitravar:
                    txt_file = file.replace('.jpeg', '.txt').replace('.jpg', '.txt').replace('.JPG', '.txt')
                    if os.path.isfile(directory_bb + txt_file):
                        f = open(directory_bb + txt_file, "r")
                        boundbox_txt = f.readline()
                        f.close()
                        img = cv2.imread(directory + file, 0)

                        ans = deteccao.get_best_marker(img, boundbox_txt)

                        if ans is None:
                            erros[object_index] += 1
                        else:
                            acertos[object_index] += 1
                            last_bar_index = ans.rfind('/')
                            if last_bar_index == -1:
                                last_bar_index = ans.rfind('\\')
                            output = directory + str(file).replace('.jpeg', '').replace('.jpg', '').replace('.JPG', '') + str(
                                resolution) + ans[last_bar_index + 1:]
                            copyfile(ans, output)
            print 'ended ' + str(objetos[object_index])

        deteccao.des = None
        deteccao.namefile_list = None
        print 'resolution ' + str(resolution)
        print 'corrects: ' + str(acertos)
        print 'wrongs: ' + str(erros)
        print ''

    print("--- time %s seconds ---" % (time.time() - start_time))