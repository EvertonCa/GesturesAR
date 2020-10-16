import numpy as np

#Object for convert positions in base of the distance between start and end be 1, meter in the case of our tests
class Converter(object):
    def __init__(self):
        self.start = None
        self.end = None
        self.Converted = 1

    #Set Slam start 3D point
    def setStart(self, firstPoint):
        self.start = firstPoint

    #Set Slam end 3D point
    def setEnd(self, lastPoint):
        self.end = lastPoint

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
    def ConvertSlamToWorld(self, xyz, distanceFactor = 1):
        xTemp = (xyz[0]*distanceFactor)/self.Converted
        yTemp = (xyz[1]*distanceFactor)/self.Converted
        zTemp = (xyz[2]*distanceFactor)/self.Converted
        xyzTemp = [xTemp, yTemp, zTemp]
        return xyzTemp

if __name__ == '__main__':
    SlamConversor = Converter()
    first = [10,0,0]
    second = [0,0,0]
    SlamConversor.setStart(first)
    SlamConversor.setEnd(second)
    SlamConversor.Converter()
    xyzSlam = [20,20,10]
    print("Distance of Slam = ", SlamConversor.Converted)
    print("SlamVector = ", xyzSlam)
    xyzSlamTemp = SlamConversor.ConvertSlamToWorld(xyzSlam)
    print("ConvertedSlamToWorld = ", xyzSlamTemp)