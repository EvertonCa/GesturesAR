import numpy as np
import os
import glob
import cv2
import numpy as np
from copy import deepcopy
import pandas as pd
import matplotlib.pyplot as plt

size_image = (4032, 3024)


def calc_iou(gt_bbox, pred_bbox):
    '''
    This function takes the predicted bounding box and ground truth bounding box and
    return the IoU ratio
    '''
    x_topleft_gt, y_topleft_gt, x_bottomright_gt, y_bottomright_gt = gt_bbox
    x_topleft_p, y_topleft_p, x_bottomright_p, y_bottomright_p = pred_bbox

    if (x_topleft_gt > x_bottomright_gt) or (y_topleft_gt > y_bottomright_gt):
        raise AssertionError("Ground Truth Bounding Box is not correct")
    if (x_topleft_p > x_bottomright_p) or (y_topleft_p > y_bottomright_p):
        raise AssertionError("Predicted Bounding Box is not correct", x_topleft_p, x_bottomright_p, y_topleft_p,
                             y_bottomright_gt)
    # if the GT bbox and predcited BBox do not overlap then iou=0

    # If bottom right of x-coordinate  GT  bbox is less than or above the top left of x coordinate of  the predicted BBox
    if (x_bottomright_gt < x_topleft_p):
        return 0.0
    # If bottom right of y-coordinate  GT  bbox is less than or above the top left of y coordinate of  the predicted BBox
    if (y_bottomright_gt < y_topleft_p):
        return 0.0
    # If bottom right of x-coordinate  GT  bbox is greater than or below the bottom right  of x coordinate of  the predcited BBox
    if (x_topleft_gt > x_bottomright_p):
        return 0.0
    # If bottom right of y-coordinate  GT  bbox is greater than or below the bottom right  of y coordinate of  the predcited BBox
    if (y_topleft_gt > y_bottomright_p):
        return 0.0

    GT_bbox_area = (x_bottomright_gt - x_topleft_gt + 1) * (y_bottomright_gt - y_topleft_gt + 1)
    Pred_bbox_area = (x_bottomright_p - x_topleft_p + 1) * (y_bottomright_p - y_topleft_p + 1)

    x_top_left = np.max([x_topleft_gt, x_topleft_p])
    y_top_left = np.max([y_topleft_gt, y_topleft_p])
    x_bottom_right = np.min([x_bottomright_gt, x_bottomright_p])
    y_bottom_right = np.min([y_bottomright_gt, y_bottomright_p])

    intersection_area = (x_bottom_right - x_top_left + 1) * (y_bottom_right - y_top_left + 1)

    union_area = (GT_bbox_area + Pred_bbox_area - intersection_area)

    return intersection_area / union_area


def yolo2coordinates(img=None, yoloparameters_txt=None, img_name=None, yolo=False):
    if img_name is None and yoloparameters_txt is None:
        return None

    if yoloparameters_txt is None:
        last_bar_index = img_name.rfind('/')
        if last_bar_index == -1:
            last_bar_index = img_name.rfind('\\')
        if yolo:
            txtfile = os.path.join(img_name[:last_bar_index], 'bb_YOLO', img_name[last_bar_index+1:])
        else:
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

    return int(xmin), int(ymin), int(xmax), int(ymax)


if __name__ == '__main__':
    rating_dictionary = {
        0: "DS4",
        1: "Groot",
        2: "MiniCraque",
        3: "PS2",
        4: "Carrinho"
    }
    
    IOU = []
    list_predict = []
    list_correct = []
    i = 0
    for directory in rating_dictionary:
        original_directory = os.path.join('SIFT_database', rating_dictionary[directory], '')
        IOU.append([])

        for file in glob.glob(original_directory + '*.jpg'):
            list_correct.append(yolo2coordinates(img_name=file, yolo=False))
            list_predict.append(yolo2coordinates(img_name=file, yolo=True))
            IOU[i].append(calc_iou(list_correct[-1], list_predict[-1]))

        print('')
        print('Media', rating_dictionary[directory], np.mean(IOU[i]))
        print('Desvio padrao', rating_dictionary[directory], np.std(IOU[i]))
        print('Variancia', rating_dictionary[directory], np.var(IOU[i]))
        i += 1
    print(IOU)
    print('')
    print('Media geral', np.mean(IOU))
    print('Desvio padrao geral', np.std(IOU))
    print('Variancia geral', np.var(IOU))

