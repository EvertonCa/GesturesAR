import cv2
import numpy as np


def get_virtual_webcam():
    cap = cv2.VideoCapture(3)
    ret, newer_frame = cap.read()
    return newer_frame.copy()


def yolo2coordinates(yolo_parameters, image_shape):
    boundbox_values = list(map(float, yolo_parameters[len(yolo_parameters) - 4:]))

    bx = boundbox_values[0] * image_shape[1]
    by = boundbox_values[1] * image_shape[0]
    bw = boundbox_values[2] * image_shape[1]
    bh = boundbox_values[3] * image_shape[0]

    xmin = bx - bw / 2
    xmax = bx + bw / 2
    ymin = by - bh / 2
    ymax = by + bh / 2

    if xmax > image_shape[1]:
        xmax = image_shape[1]
    if xmin < 0:
        xmin = 0
    if ymax > image_shape[0]:
        ymax = image_shape[0]
    if ymin < 0:
        ymin = 0

    return int(xmin), int(ymin), int(xmax), int(ymax)


def object_detection(yolo_output, marker_name='Marker/Marker.png'):
    print yolo_output
    yolo_output = yolo_output.replace('\t', '').replace('Object Detected: ', '').replace('(center_x:', '').replace(
        '  center_y: ', '').replace('  width: ', '').replace('  height: ', '').replace(')', '').replace('\n',
                                                                                                        '').replace(
        '%', '').replace(':', '')

    yolo_parameters = yolo_output.split(' ')

    frame = get_virtual_webcam()

    bb = yolo2coordinates(yolo_parameters, frame.shape)

    if bb is None:
        return None

    cv2.imwrite(marker_name, frame[bb[1]:bb[3], bb[0]:bb[2]])

    return marker_name


if __name__ == '__main__':
    yolo_bb = input("Insert YOLO bounding box:\n")

    if len(yolo_bb) >= 0:
        object_detection(yolo_bb)
