import numpy as np

# Object for convert positions in base of the distance between first and Second be 1, meter in the case of our tests
class DistanceCalibrator(object):
    def __init__(self):
        self.first = None
        self.Second = None
        self.converted = 1
        self.ready = False

    #Set Hands first 3D point
    def setfirst(self, x, y, z):
        self.first = [float(x), float(y), float(z)]
        print(str(self.first) + " --------------------------------------------------------- ")

    #Set Hands Second 3D point
    def setSecond(self, x, y, z):
        self.Second = [float(x), float(y), float(z)]
        print(str(self.Second) + " --------------------------------------------------------- ")

    #Convert both points into the number equivalent to 1, meter in the case of our tests

    def calibrate(self):
        #euclidean distance between 2 3d points
        self.converted = np.sqrt((np.power(self.Second[0] - self.first[0], 2)) + (np.power(self.Second[1] - self.first[1], 2)) + (np.power(self.Second[2] - self.first[2], 2)))
        print("Fator de conversao = " + str(self.converted))
        self.ready = True

    #Distance factor default is 1 meter
    def convertHands(self, hands, distanceFactor = 1):
        self.setfirst(hands[0][0],hands[0][1], hands[0][2])
        self.setSecond(hands[9][0], hands[9][1], hands[9][2])
        self.calibrate()
        handsConverted = np.zeros((21, 3))
        for i in range(21):
            for j in range(3):
                handsConverted[i][j] = (float(hands[i][j])*distanceFactor)/self.converted
        return handsConverted

if __name__ == '__main__':
    handsPoints = np.array([[-193.2427062988281, -177.984619140625, 253.4805603027344], [
 -174.5455169677734, -154.5236968994141, 253.4585418701172], [
 -174.5455169677734, -154.5236968994141, 253.4585418701172], [
 -139.5068511962891, -152.4359436035156, 295.8015747070312], [
 -120.3824081420898, -141.3369903564453, 326.7057495117188], [
 -98.26676940917969, -148.6035766601562, 352.8418579101562], [
 -172.2418975830078, -96.36979675292969, 264.5705261230469], [
 -172.2418975830078, -96.36979675292969, 264.5705261230469], [
 -160.7995910644531, -48.78924560546875, 274.8255310058594], [
 -154.5304870605469, -19.50054359436035, 276.5197143554688], [
 -149.2319946289062, 2.446422576904297, 265.783935546875], [
 -192.0698852539062, -78.48229217529297, 263.3755798339844], [
 -192.0698852539062, -78.48229217529297, 263.3755798339844], [
 -195.3451995849609, -19.43167877197266, 273.4898071289062], [
 -197.2812042236328, 17.07278823852539, 279.2060546875], [
 -189.5502777099609, 29.21732521057129, 256.3643493652344], [
 -208.9097137451172, -94.70769500732422, 260.1512451171875], [
 -208.9097137451172, -94.70769500732422, 260.1512451171875], [
 -217.2839050292969, -38.41407775878906, 263.2980346679688], [
 -222.1207427978516, -5.808574676513672, 261.7210998535156], [
 -220.6122131347656, 17.46219444274902, 250.2234649658203], [
 -225.2716064453125, -97.09560394287109, 253.8245086669922], [
 -225.2716064453125, -97.09560394287109, 253.8245086669922], [
 -247.9626007080078, -61.02262878417969, 259.5567932128906], [
 -255.6140289306641, -40.91355133056641, 254.9654235839844], [
 -261.1300354003906, -19.67850494384766, 248.0627899169922]])
    hands = DistanceCalibrator()
    handsResult = hands.convertHands(handsPoints)
    print("Hands Enter = ", handsPoints)
    print("Hands Exit = ", handsResult)