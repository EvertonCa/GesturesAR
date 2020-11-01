import numpy as np

# Object for convert positions in base of the distance between start and end be 1, meter in the case of our tests
class DistanceCalibrator(object):
    def __init__(self):
        self.start = None
        self.end = None
        self.converted = 1
        self.ready = False

    #Set Slam start 3D point
    def setStart(self, x, y, z):
        self.start = [float(x), float(y), float(z)]
        print "Calibration start at: " + str(self.start)

    #Set Slam end 3D point
    def setEnd(self, x, y, z):
        self.end = [float(x), float(y), float(z)]
        self.calibrate()
        print "Calibration end at: " + str(self.end)

    #Set Converted
    #def setConverted(self, value):
     #   self.Converted = value

    #Convert both points into the number equivalent to 1, meter in the case of our tests

    def calibrate(self):
        #if self.start != None and self.end != None:
        #euclidean distance between 2 3d points
        self.converted = np.sqrt((np.power(self.end[0] - self.start[0], 2)) + (np.power(self.end[1] - self.start[1], 2)) + (np.power(self.end[2] - self.start[2], 2)))
        self.converted /= 25.4
        self.ready = True
        #distance between 2 2D points
        #self.Converted = np.sqrt((np.power(self.end[0] - self.start[0], 2))+(np.power(self.end[1] - self.start[1], 2)))

    #Distance factor default is 1 meter
    def convertSlamToWorld(self, x, y, z, distanceFactor = 1):
        xTemp = (float(x)*distanceFactor)/self.converted
        yTemp = (float(y)*distanceFactor)/self.converted
        zTemp = (float(z)*distanceFactor)/self.converted
        return [xTemp, yTemp, zTemp]
