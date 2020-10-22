import numpy as np

#Object for convert positions in base of the distance between start and end be 1, meter in the case of our tests
class Converter(object):
    def __init__(self):
        self.start = None
        self.end = None
        self.Converted = 1

    #Set Slam start 3D point
    def setStart(self, x, y, z):
        self.start = [float(x),float(y),float(z)]

    #Set Slam end 3D point
    def setEnd(self, x, y, z):
        self.end = [float(x),float(y),float(z)]
        self.Converter()

    #Set Converted
    #def setConverted(self, value):
     #   self.Converted = value

    #Convert both points into the number equivalent to 1, meter in the case of our tests

    def Converter(self):
        #if self.start != None and self.end != None:
        #euclidean distance between 2 3d points
        self.Converted = np.sqrt((np.power(self.end[0] - self.start[0], 2))+(np.power(self.end[1] - self.start[1], 2))+(np.power(self.end[2] - self.start[2], 2)))
        #distance between 2 2D points
        #self.Converted = np.sqrt((np.power(self.end[0] - self.start[0], 2))+(np.power(self.end[1] - self.start[1], 2)))

    #Distance factor default is 1 meter
    def ConvertSlamToWorld(self, x, y, z, distanceFactor = 1):
        xTemp = (float(x)*distanceFactor)/self.Converted
        yTemp = (float(y)*distanceFactor)/self.Converted
        zTemp = (float(z)*distanceFactor)/self.Converted
        return [xTemp, yTemp, zTemp]
