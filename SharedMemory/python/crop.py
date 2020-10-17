import numpy as np
import cv2


def crop_image(I, polygon):
    # First find the minX minY maxX and maxY of the polygon
    minX = I.shape[1]
    maxX = -1
    minY = I.shape[0]
    maxY = -1
    for point in polygon[0]:

        x = point[0]
        y = point[1]

        if x < minX:
            minX = x
        if x > maxX:
            maxX = x
        if y < minY:
            minY = y
        if y > maxY:
            maxY = y
    if minX < 0:
        minX = 0
    if maxX > I.shape[1]:
        maxX = I.shape[1]
    if minY < 0:
        minY = 0
    if maxY > I.shape[0]:
        maxY = I.shape[0]

    # Go over the points in the image if not check if thay are inside the polygon or not
    cropedImage = np.zeros_like(I)

    for y in range(minY, maxY):
        for x in range(minX, maxX):
            if cv2.pointPolygonTest(np.asarray(polygon), (x, y), False) >= 0:
                cropedImage[y, x, 0] = I[y, x, 0]
                cropedImage[y, x, 1] = I[y, x, 1]
                cropedImage[y, x, 2] = I[y, x, 2]

    # Now we can crop again just the envloping rectangle
    finalImage = cropedImage[minY:maxY, minX:maxX]

    # Now strectch the polygon to a rectangle. We take the points that
    polygonStrecth = np.float32(
        [[0, 0], [finalImage.shape[1], 0], [finalImage.shape[1], finalImage.shape[0]], [0, finalImage.shape[0]]])

    # Convert the polygon corrdanite to the new rectnagle
    polygonForTransform = np.zeros_like(polygonStrecth)
    i = 0
    for point in polygon[0]:
        x = point[0]
        y = point[1]

        newX = x - minX
        newY = y - minY

        polygonForTransform[i] = [newX, newY]
        i += 1
    # Find affine transform
    M = cv2.getPerspectiveTransform(np.asarray(polygonForTransform).astype(np.float32),
                                    np.asarray(polygonStrecth).astype(np.float32))

    if minY == maxY or minX == maxX:
        return None
    # Warp one image to the other
    warpedImage = cv2.warpPerspective(finalImage, M, (finalImage.shape[1], finalImage.shape[0]))

    return warpedImage


if __name__ == '__main__':
    name_img1 = 'imgteste.png'
    img1 = cv2.imread(name_img1)

    # Define the polygon coordinates to use or the crop
    polygon = [[[20, 110], [450, 108], [340, 420], [125, 420]]]

    crop_image(img1, polygon)