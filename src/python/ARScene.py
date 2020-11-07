import sys
from Queue import Queue
from direct.gui.OnscreenText import OnscreenText
from direct.interval.LerpInterval import LerpFunc
from panda3d.core import OccluderNode, loadPrcFileData, CardMaker, MovieTexture, Filename, Point2, TextNode, CollisionTraverser, \
    CollisionHandlerQueue, CollisionHandlerPusher, CollisionNode, BitMask32, LVecBase3f, LQuaternion, \
    CollisionSphere, NodePath, PStatClient, Texture, CollisionBox, LPoint3f, LVecBase3, CollisionPolygon, CollisionTube
from direct.showbase.ShowBase import ShowBase
from panda3d.vision import WebcamVideo, ARToolKit
from DistanceCalibrator import DistanceCalibrator
from HorizontalPlaneCorrection import send_factor_to_slam
from ObjectDetection import object_detection
from threading import Thread
from subprocess import Popen
import os
import numpy as np
import time
from panda3d.core import AmbientLight, DirectionalLight, LightAttrib, LVector3
from math import pi, sin
from direct.interval.FunctionInterval import Func, Wait
from direct.interval.LerpInterval import LerpFunc
from direct.interval.MetaInterval import Sequence, Parallel

METER = 25.4

loadPrcFileData("", "textures-power-2 none")  #the webcam feed can not be made into a power of two texture
#loadPrcFileData("", "show-frame-rate-meter 1") #show fps
loadPrcFileData("", "sync-video 0") #turn off v-sync
loadPrcFileData("", "auto-flip 1") #usualy the drawn texture lags a bit behind the calculted positions. this is a try to reduce the lag.

canUpdateYOLO = True
canUpdatePlane = True
canUpdateHands = False
canUpdateSlam = False
isObjectCreated = False

calibrated = False

markerCreated = False

positionArray = []
globalCounter = 0

ganPositionArray = []

globalGanCounter = 0
actualGanJoint = 0

yoloBB = ""
plane = ""

cam_resolution = [1280, 720]

sizeimg_database = [2048, 1536]
objectsize = [[0.40, 0.306640625, 0.26432291666666666666666666666667], [0.40, 0.2197265625, 0.375], [0.40, 0.228515625, 0.19661458333333333333333333333333], [0.40, 0.6328125, 58072916666666666666666666666667], [0.40, 0.51953125, 0.30729166666666666666666666666667]]
proportion_bb2cm = [0.51953125, 0.30729166666666666666666666666667, 0.185, 0.06]

queueSlam = Queue()
queueSlamCalibrated = Queue()
queueHands = Queue()


def genLabelText(text, i, self):
    return OnscreenText(text=text, parent=self.a2dTopLeft, scale=.04,
                        pos=(0.06, -.08 * i), fg=(1, 1, 1, 1),
                        shadow=(0, 0, 0, .5), align=TextNode.ALeft)


def updateYOLO(text):
    global canUpdateYOLO
    global yoloBB

    if len(text) > 0:
        if canUpdateYOLO:
            yoloBB = text


def updatePlane(text):
    global canUpdatePlane
    global plane

    if len(text) > 0:
        if canUpdatePlane:
            plane = text


def updateSlam(text):
    global positionArray
    global globalCounter
    global queueSlam
    global queueSlamCalibrated
    global calibrated
    global initialClock

    if len(text) > 0:
        splitedString = text.split()
        globalCounter = int(splitedString[0])
        x = float(splitedString[1])
        y = float(splitedString[2])
        z = float(splitedString[3])
        qx = float(splitedString[4])
        qy = float(splitedString[5])
        qz = float(splitedString[6])
        qw = float(splitedString[7])
        vector3f = LVecBase3f(x, z, -y)
        quaternion = LQuaternion(qw, qx, qz, -qy)
        cameraPos = [vector3f, quaternion, int(splitedString[0])]
        positionArray = cameraPos
        if calibrated:
            queueSlamCalibrated.put(positionArray)
        else:
            queueSlam.put(positionArray)
        #print "SLAM - " + str(time() - initialClock) + str(positionArray)
        #print "Fora " + str(positionArray) + " - Frame: " + splitedString[0]
        #print "FORA " + str(globalCounter) + str(canUpdateSlam)


def updateHands(text):
    global ganPositionArray
    global queueHands
    global canUpdateHands

    if canUpdateHands:
        ganPositionArray = []
        splitText = text.split('][')

        for i, line in enumerate(splitText):
            temp = line.replace('"', '').replace('[', '').replace(',', '').replace(';', '').\
                replace(']', '').replace('\n', '')
            if len(temp) > 2:
                xt, yt, zt = temp.split(" ")
                # Center of GanHands (493,y,-127)
                a = float(xt)
                b = float(yt)
                c = float(zt)
                # if i == 8:
                #     print "Ponto " + str(i) + " puro: " + str(a) + " " + str(c) + " " + str(b)
                x = (-(a / 1000) * METER) - 8.0
                y = (c / 1000) * METER * 5.0
                z = ((b / 1000) * METER) + 5.0
                # if i == 8:
                #     print "Ponto " + str(i) + " convertido: " + str(x) + " " + str(y) + " " + str(z)
                vector3f = LVecBase3f(x, y, z)
                ganPositionArray.append(vector3f)
                queueHands.put(vector3f)


class ARScene(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.dice_colision = None
        self.dice = None
        self.surface_box = None
        self.palm = None

        self.cleanQueue = False

        self.label_yolo = {
            'Dualshock4': 0,
            'IamGroot': 1,
            'MiniCraque': 2,
            'PlayStation2': 3,
            'Carrinho': 4
        }

        self.calibrator = DistanceCalibrator()

        self.cTrav = CollisionTraverser()

        self.cHandler = CollisionHandlerQueue()

        self.pusher = CollisionHandlerPusher()

        self.generateText()

        self.defineKeys()

        self.title = OnscreenText(text="TCC Simulation",
                                  fg=(1, 1, 1, 1), parent=self.a2dBottomRight,
                                  align=TextNode.ARight, pos=(-0.1, 0.1),
                                  shadow=(0, 0, 0, .5), scale=.08)

        #Windows WebCam
        option = WebcamVideo.getOption(296)  # 0 here is default webcam, 1 would be second cam etc.
        self.tex = MovieTexture(option)
        self.tex.setTexturesPower2(0)
        self.tex.setKeepRamImage(True)

        print("WebCamVideo based texture infos: -> {0}".format(self.tex))

        # create a card which shows the image captured by the webcam.
        cm = CardMaker("background-card")
        cm.setUvRange(Point2(0, 0), Point2(1, 1))
        cm.setFrame(-1, 1, -1, 1)
        card = self.render2d.attachNewNode(cm.generate())
        card.setTexture(self.tex)

        # set the rendering order manually to render the card-with the webcam-image behind the scene.
        self.cam.node().getDisplayRegion(0).setSort(20)

        # initialize artoolkit, self.cam is our camera ,
        # the camera_para.dat is the configuration file for your camera. this one comes with the artoolkit installation.
        # last parameter is the size of the pattern in panda-units.
        self.ar = ARToolKit.make(self.cam, Filename(self.mainDir, "ar/camera_para.dat"), 0)

        # variables for the system
        self.axis = self.loader.loadModel("models/ball")
        self.ballSphere = self.axis.find("**/ball")
        self.ganNodes = {}
        self.setGanNodes()

        self.ganCollisions = {}
        self.cilinder = {}
        self.define_capsule_collision()
        self.define_cilinders()

        self.startSlam()

    def startSlam(self):
        self.taskMgr.add(self.refreshCameraPosition, "refresh-camera-position", sort=0, priority=0)

    def addObject(self):
        self.axis.reparentTo(self.render)
        self.axis.setScale(0.5, 0.5, 0.5)
        self.ballSphere2 = self.axis.find("**/ball")
        self.ballSphere2.node().setFromCollideMask(BitMask32.bit(1))
        self.ballSphere2.node().setIntoCollideMask(BitMask32.allOff())
        self.ballSphere2.show()

        self.cTrav.addCollider(self.ballSphere2, self.pusher)

        self.pusher.addCollider(self.ballSphere2, self.axis, self.drive.node())

        # attach the model to a pattern so it updates the model's position relative to the camera each time we call analyze()
        self.ar.attachPattern(Filename(self.mainDir, "Marker/patt.kanji"), self.axis)
        #self.ar.attachPattern(Filename(self.mainDir, "ar/groot_720.patt"), self.axis)
        self.taskMgr.add(self.updatePatterns, "update-patterns")
        print "Pattern loaded"

    def activeAr(self):
        print self.cam.getPos()

    def detachObjetct(self):
        self.ar.detachPatterns()
        print("Object position now: " + str(self.axis.getPos()))

    def updatePatterns(self, task):
        self.ar.analyze(self.tex, True)
        return task.cont

    def initHands(self):
        global canUpdateHands

        canUpdateHands = True
        self.taskMgr.add(self.setGanNodesPosition, "set-gan-nodes-position")

    def setGanNodesPosition(self, task):
        global queueHands
        if not queueHands.empty():
            if self.calibrator.ready:
                for i in range(21):
                    ganVector3f = queueHands.get()
                    x = ganVector3f.getX()
                    y = ganVector3f.getY()
                    z = ganVector3f.getZ()
                    calibratedVector3f = LVecBase3f(x, y, z)
                    self.ganNodes["Node" + str(i)].setPos(calibratedVector3f)
                    self.ganNodes["Node" + str(i)].show()

                    self.set_capsule_colision(i)
                    self.set_cilinder_position(i)

                #print("Coordenadas Camera: " + str(self.cam.getPos()) + "\n")
        return task.cont

    def set_capsule_colision(self, i):
        if i == 0:
            return
        elif i % 4 == 1:
            self.ganCollisions["Collision{0}".format(i)].node().modifySolid(0).setPointA(
                self.ganNodes["Node{0}".format(0)].getPos(self.cam) - self.ganNodes["Node{0}".format(i)].getPos(self.cam))
        else:
            self.ganCollisions["Collision{0}".format(i)].node().modifySolid(0).setPointA(
                self.ganNodes["Node{0}".format(i-1)].getPos(self.cam) - self.ganNodes["Node{0}".format(i)].getPos(self.cam))

        self.ganCollisions["Collision{0}".format(i)].show()

    def set_cilinder_position(self, i):
        if i == 0:
            return
        elif i % 4 == 1:
            self.cilinder["Cilinder{0}".format(i)].setPos(
                (self.ganNodes["Node{0}".format(0)].getPos() - self.ganNodes["Node{0}".format(i)].getPos()) / 2)
            p1 = (self.ganNodes["Node{0}".format(0)].getX(), self.ganNodes["Node{0}".format(0)].getY(),
                  self.ganNodes["Node{0}".format(0)].getZ())
            p2 = (self.ganNodes["Node{0}".format(i)].getX(), self.ganNodes["Node{0}".format(i)].getY(),
                  self.ganNodes["Node{0}".format(i)].getZ())
            eudi = self.euclidian_distance(p1, p2)
            self.cilinder["Cilinder{0}".format(i)].setScale((0.20, 0.20, eudi))
        else:
            self.cilinder["Cilinder{0}".format(i)].setPos(
                (self.ganNodes["Node{0}".format(i - 1)].getPos() - self.ganNodes["Node{0}".format(i)].getPos()) / 2)
            p1 = (self.ganNodes["Node{0}".format(i - 1)].getX(), self.ganNodes["Node{0}".format(i - 1)].getY(),
                  self.ganNodes["Node{0}".format(i - 1)].getZ())
            p2 = (self.ganNodes["Node{0}".format(i)].getX(), self.ganNodes["Node{0}".format(i)].getY(),
                  self.ganNodes["Node{0}".format(i)].getZ())
            eudi = self.euclidian_distance(p1, p2)
            self.cilinder["Cilinder{0}".format(i)].setScale((0.20, 0.20, eudi))
        self.cilinder["Cilinder{0}".format(i)].lookAt(self.ganNodes["Node{0}".format(i)])
        self.cilinder["Cilinder{0}".format(i)].setP(self.cilinder["Cilinder{0}".format(i)].getP() + 90)

    def euclidian_distance(self, start, end):
        eudi = np.sqrt((np.power(end[0] - start[0], 2)) + (np.power(end[1] - start[1], 2)) + (
            np.power(end[2] - start[2], 2)))
        return eudi

    def define_capsule_collision(self):
        for i in range(1, 21):
            cNode = CollisionNode("Collision" + str(i))
            cNode.addSolid(CollisionTube(0, 0, 0, 0, 0, 0, 0.1))
            nodePath = NodePath("NodePathCollision{0}".format(i))
            self.ganCollisions["Collision{0}".format(i)] = nodePath.attachNewNode(cNode)
            self.ganCollisions["Collision{0}".format(i)].reparentTo(self.ganNodes["Node{0}".format(i)])

    def define_cilinders(self):
        for i in range(1, 21):
            self.cilinder["Cilinder{0}".format(i)] = self.loader.loadModel("models/cilindro")

            self.cilinder["Cilinder{0}".format(i)].reparentTo(self.ganNodes["Node{0}".format(i)])

            self.cilinder["Cilinder{0}".format(i)].setScale(0.25, 0.25, 0.25)

            self.cilinder["Cilinder{0}".format(i)].setPos(0, 0, 0)

    def setGanNodes(self):
        for i in range(21):
            cNode = CollisionNode("GanNode" + str(i))
            cNode.addSolid(CollisionSphere(0, 0, 0, 0.1))
            nodePath = NodePath("NodePath{0}".format(i))
            self.ganNodes["Node{0}".format(i)] = nodePath.attachNewNode(cNode)
            self.ganNodes["Node{0}".format(i)].reparentTo(self.cam)

    def refreshCameraPosition(self, task):
        global positionArray
        global globalCounter
        global queueSlam
        global calibrated
        global queueSlamCalibrated

        if calibrated:
            if not queueSlamCalibrated.empty():
                array = queueSlamCalibrated.get()
                #print str(array)
                temp2 = self.calibrator.convertSlamToWorld(array[0].getX(), array[0].getY(), array[0].getZ())
                temp = LVecBase3f(temp2[0], temp2[1], temp2[2])
                array[0] = temp
                quaternion = LQuaternion(array[1][0], array[1][1], array[1][2], array[1][3])
                #print "Camera position " + str(array[0]) + " Quaternion " + str(quaternion)
                self.cam.setPosQuat(array[0], quaternion)
        else:
            if not queueSlam.empty():
                array = queueSlam.get()
                quaternion = LQuaternion(array[1][0], array[1][1], array[1][2], array[1][3])
                #print "Camera position non calibrated " + str(array[0]) + " Quaternion " + str(quaternion)
                self.cam.setPosQuat(array[0], quaternion)
        return task.cont

    def verifyVirtualObject(self):
        global isObjectCreated

        if self.calibrator.ready:
            if not isObjectCreated:
                x = self.cam.getX(self.render)
                y = self.cam.getY(self.render)
                z = self.cam.getZ(self.render)

                scale = [1, 1, 1]

                if self.surface_box is not None:
                    pos = [self.surface_box.getX(), self.surface_box.getY(), self.surface_box.getZ() + (self.surface_box.getSz() + 1.8*scale[2]) / 2]
                else:
                    pos = [x, y + 30, z]

                self.load_carrossel(pos, scale)
                self.setupLights()
                self.startCarousel()
                print self.carousel.getPos(self.render)
                print self.carousel.getPos(self.cam)
                #cNode = CollisionNode("DiceNode")
                #cNode.addSolid(CollisionBox(self.dice.getPos(), 0.15, 0.15, 0.15))
                #nodePath = NodePath("NodePathDice")
                #self.dice_colision = nodePath.attachNewNode(cNode)
                #self.dice_colision.reparentTo(self.render)
                #self.dice_colision.node().setFromCollideMask(BitMask32.bit(1))
                #self.dice_colision.node().setIntoCollideMask(BitMask32.allOff())

                #self.cTrav.addCollider(self.dice_colision, self.pusher)

                #self.pusher.addCollider(self.dice_colision, self.dice, self.drive.node())
                self.cTrav.showCollisions(self.render)

                isObjectCreated = True

    def startCalibration(self):
        x = self.cam.getX()
        y = self.cam.getY()
        z = self.cam.getZ()

        self.calibrator.setStart(x, y, z)

    def endCalibration(self):
        global calibrated

        x = self.cam.getX()
        y = self.cam.getY()
        z = self.cam.getZ()

        self.calibrator.setEnd(x, y, z)

        # sends the right dimensions to slam
        send_factor_to_slam(self.calibrator.converted)
        calibrated = True

    def detect_object(self):
        global canUpdateYOLO
        global yoloBB
        global markerCreated

        canUpdateYOLO = False
        marker_thread = Thread(target=object_detection, args=(yoloBB, ))
        marker_thread.start()
        marker_thread.join()
        yolo_output = yoloBB.replace('\t', '').replace('Object Detected: ', '').replace('(center_x:', '').replace(
            '  center_y: ', '').replace('  width: ', '').replace('  height: ', '').replace(')', '').replace('\n',
                                                                                                            '').replace(
            '%', '').replace(':', '')

        yolo_parameters = yolo_output.split(' ')
        label_number = self.label_yolo[yolo_parameters[0]]
        y = objectsize[label_number][0]*objectsize[label_number][2]*sizeimg_database[1]/(float(yolo_parameters[3]) *
                                                                                       sizeimg_database[1])
        y *= METER*5

        distance_center = (float(yolo_parameters[2]) - 0.5)*sizeimg_database[0]
        x = proportion_bb2cm[2] * distance_center / (proportion_bb2cm[0]*sizeimg_database[0])
        x *= METER*5

        distance_center = (float(yolo_parameters[3]) - 0.5)*sizeimg_database[1]
        z = proportion_bb2cm[3] * distance_center / (proportion_bb2cm[1]*sizeimg_database[1])
        z *= METER*5

        temp = self.loader.loadModel("models/Dice_Obj.obj")
        tex = self.loader.loadTexture('models/Dice_Base_Color.png')
        tex.setWrapV(Texture.WM_repeat)
        temp.setTexture(tex, 2)
        temp.reparentTo(self.cam)
        temp.setScale(1, 1, 1)
        temp.setPos(x, y, z)

        worldPosition = temp.getPos(self.render)
        worldQuat = temp.getQuat(self.render)

        temp.reparentTo(self.render)
        temp.setPos(worldPosition)
        temp.setQuat(worldQuat)
        print "Cubo em metros = " + str([x/METER, y/METER, z/METER])
        print 'camera em ' + str(self.cam.getPos())
        print "Cubo em relacao camera " + str(temp.getPos(self.cam))

        canUpdateYOLO = True
        if os.path.exists('Marker/Marker.png'):
            markerCreated = True

    def set_plane(self):
        grid_thread = Thread(target=self.set_grid, args=())
        grid_thread.start()

    def set_grid(self):
        global plane
        non_zero_points = list()

        while len(non_zero_points) <= 2:
            points = plane
            if points == '':
                return
            points = points.split(' ')
            points = list(map(float, points))
            print "Pontos do plano SLAM: " + str(points)
            points = np.reshape(points, [4, 3])

            for i in range(4):
                point_word = self.calibrator.convertSlamToWorld(points[i][0], points[i][2], -points[i][1])
                print 'WORLD Ponto' + str(i) + ' = ' + str(point_word)

                if not ((points[i][0] == points[i][1] and points[i][1] == points[i][2]) or
                        (point_word in non_zero_points)):
                    non_zero_points.append(point_word)
            if len(non_zero_points) <= 2:
                print "Insufficient points"
                non_zero_points = list()
                time.sleep(0.033)

        non_zero_points = np.transpose(non_zero_points)
        print non_zero_points
        points_mean = np.mean(non_zero_points, 1)

        x, y, z = points_mean[0], points_mean[1], points_mean[2]
        print "Centro do plano colocado em x: " + str(x) + " y: " + str(y) + " z: " + str(z)
        dx, dy, dz = 8, 8, 0.01

        print "Coordenadas Camera: " + str(self.cam.getPos()) + "\n"

        self.surface_box = self.loader.loadModel('models/cube.obj')
        self.surface_box.reparentTo(self.render)
        tex = self.loader.loadTexture('models/iron05.jpg')
        tex.setWrapU(Texture.WM_repeat)
        self.surface_box.setTexture(tex, 2)
        self.surface_box.setPos(x, y, z - dz)
        self.surface_box.setScale(dx, dy, dz)

        cNode = CollisionNode("SurfaceNode")
        cNode.addSolid(CollisionBox(LPoint3f(x, y, z - dz), dx, dy, dz))
        nodePath = NodePath("NodePath")
        self.collision_surface = nodePath.attachNewNode(cNode)
        self.collision_surface.reparentTo(self.render)

    def load_carrossel(self, pos, scale):
        self.modelandcollision = NodePath("NodePathCarouselAndCollision")
        self.modelandcollision.setPos(pos[0], pos[1], pos[2])
        self.modelandcollision.reparentTo(self.render)
        # Load the carousel base
        self.carousel = self.loader.loadModel("models/carousel_base")
        self.carousel.setScale(scale[0], scale[1], scale[2])
        self.carousel.reparentTo(self.modelandcollision)

        # Load the modeled lights that are on the outer rim of the carousel
        # (not Panda lights)
        # There are 2 groups of lights. At any given time, one group will have
        # the "on" texture and the other will have the "off" texture.
        self.lights1 = self.loader.loadModel("models/carousel_lights")
        self.lights1.reparentTo(self.carousel)

        # Load the 2nd set of lights
        self.lights2 = self.loader.loadModel("models/carousel_lights")
        # We need to rotate the 2nd so it doesn't overlap with the 1st set.
        self.lights2.setH(36)
        self.lights2.reparentTo(self.carousel)

        # Load the textures for the lights. One texture is for the "on" state,
        # the other is for the "off" state.
        self.lightOffTex = self.loader.loadTexture("models/carousel_lights_off.jpg")
        self.lightOnTex = self.loader.loadTexture("models/carousel_lights_on.jpg")

        # Create an list (self.pandas) with filled with 4 dummy nodes attached
        # to the carousel.
        # This uses a python concept called "Array Comprehensions."  Check the
        # Python manual for more information on how they work
        self.pandas = [self.carousel.attachNewNode("panda" + str(i))
                       for i in range(4)]
        self.models = [self.loader.loadModel("models/carousel_panda")
                       for i in range(4)]
        self.moves = [0] * 4

        for i in range(4):
            # set the position and orientation of the ith panda node we just created
            # The Z value of the position will be the base height of the pandas.
            # The headings are multiplied by i to put each panda in its own position
            # around the carousel
            self.pandas[i].setPosHpr(0, 0, 1.3, i * 90, 0, 0)

            # Load the actual panda model, and parent it to its dummy node
            self.models[i].reparentTo(self.pandas[i])
            # Set the distance from the center. This distance is based on the way the
            # carousel was modeled in Maya
            self.models[i].setY(.85)

        cNode = CollisionNode('carouselCollision')
        cNode.addSolid(CollisionSphere(0, 0, self.models[1].getZ(self.carousel), 1.8 * scale[0]))
        self.carouselC = self.carousel.attachNewNode(cNode)
        #self.carouselC.show()

        self.cTrav.addCollider(self.carouselC, self.pusher)
        # self.carouselC.node().setFromCollideMask(BitMask32.bit(1))
        # self.carouselC.node().setIntoCollideMask(BitMask32.allOff())
        self.pusher.addCollider(self.carouselC, self.carousel, self.drive.node())

    def setupLights(self):
        # Create some lights and add them to the scene. By setting the lights on
        # render they affect the entire scene
        # Check out the lighting tutorial for more information on lights
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor((.4, .4, .35, 1))
        directionalLight = DirectionalLight("directionalLight")
        directionalLight.setDirection(LVector3(0, 8, -2.5))
        directionalLight.setColor((0.9, 0.8, 0.9, 1))
        self.render.setLight(self.render.attachNewNode(directionalLight))
        self.render.setLight(self.render.attachNewNode(ambientLight))

    def startCarousel(self):
        # Here's where we actually create the intervals to move the carousel
        # The first type of interval we use is one created directly from a NodePath
        # This interval tells the NodePath to vary its orientation (hpr) from its
        # current value (0,0,0) to (360,0,0) over 20 seconds. Intervals created from
        # NodePaths also exist for position, scale, color, and shear

        self.carouselSpin = self.carousel.hprInterval(20, LVector3(360, 0, 0))
        # Once an interval is created, we need to tell it to actually move.
        # start() will cause an interval to play once. loop() will tell an interval
        # to repeat once it finished. To keep the carousel turning, we use
        # loop()
        self.carouselSpin.loop()

        # The next type of interval we use is called a LerpFunc interval. It is
        # called that becuase it linearly interpolates (aka Lerp) values passed to
        # a function over a given amount of time.

        # In this specific case, horses on a carousel don't move contantly up,
        # suddenly stop, and then contantly move down again. Instead, they start
        # slowly, get fast in the middle, and slow down at the top. This motion is
        # close to a sine wave. This LerpFunc calls the function oscillatePanda
        # (which we will create below), which changes the height of the panda based
        # on the sin of the value passed in. In this way we achieve non-linear
        # motion by linearly changing the input to a function
        for i in range(4):
            self.moves[i] = LerpFunc(
                self.oscillatePanda,  # function to call
                duration=3,  # 3 second duration
                fromData=0,  # starting value (in radians)
                toData=2 * pi,  # ending value (2pi radians = 360 degrees)
                # Additional information to pass to
                # self.oscialtePanda
                extraArgs=[self.models[i], pi * (i % 2)]
            )
            # again, we want these to play continuously so we start them with
            # loop()
            self.moves[i].loop()

        # Finally, we combine Sequence, Parallel, Func, and Wait intervals,
        # to schedule texture swapping on the lights to simulate the lights turning
        # on and off.
        # Sequence intervals play other intervals in a sequence. In other words,
        # it waits for the current interval to finish before playing the next
        # one.
        # Parallel intervals play a group of intervals at the same time
        # Wait intervals simply do nothing for a given amount of time
        # Func intervals simply make a single function call. This is helpful because
        # it allows us to schedule functions to be called in a larger sequence. They
        # take virtually no time so they don't cause a Sequence to wait.

        self.lightBlink = Sequence(
            # For the first step in our sequence we will set the on texture on one
            # light and set the off texture on the other light at the same time
            Parallel(
                Func(self.lights1.setTexture, self.lightOnTex, 1),
                Func(self.lights2.setTexture, self.lightOffTex, 1)),
            Wait(1),  # Then we will wait 1 second
            # Then we will switch the textures at the same time
            Parallel(
                Func(self.lights1.setTexture, self.lightOffTex, 1),
                Func(self.lights2.setTexture, self.lightOnTex, 1)),
            Wait(1)  # Then we will wait another second
        )

        self.lightBlink.loop()  # Loop this sequence continuously

    def oscillatePanda(self, rad, panda, offset):
        # This is the oscillation function mentioned earlier. It takes in a
        # degree value, a NodePath to set the height on, and an offset. The
        # offset is there so that the different pandas can move opposite to
        # each other.  The .2 is the amplitude, so the height of the panda will
        # vary from -.2 to .2
        panda.setZ(sin(rad + offset) * .2)

    def imprime(self):
        print 'Node0 ' + str(self.ganNodes['Node0'].getPos(self.render))
        print 'Node4 ' + str(self.ganNodes['Node4'].getPos(self.render))
        print 'Node12 ' + str(self.ganNodes['Node12'].getPos(self.render))
        print 'Node20 ' + str(self.ganNodes['Node20'].getPos(self.render))

    def showpoints(self):
        global plane
        points = plane
        if points == '':
            return
        points = points.split(' ')
        points = list(map(float, points))
        print "Pontos do plano SLAM: " + str(points)
        points = np.reshape(points, [4, 3])

        non_zero_points = list()

        for i in range(4):
            ponto = self.calibrator.convertSlamToWorld(points[i][0], points[i][2], -points[i][1])

            if not (points[i][0] == points[i][1] and points[i][1] == points[i][2]):
                non_zero_points.append(ponto)

        for j in non_zero_points:
            temp = self.loader.loadModel("models/Dice_Obj.obj")
            tex = self.loader.loadTexture('models/Dice_Base_Color.png')
            tex.setWrapV(Texture.WM_repeat)
            temp.setTexture(tex, 2)
            temp.reparentTo(self.render)
            temp.setScale(1, 1, 1)
            temp.setPos(j[0], j[1], j[2])
            print "Ponto em " + str(j)
            print "Objeto vs mundo: " + str(temp.getPos())
            print "Objeto vs camera: " + str(temp.getPos(self.cam))
        print "Camera em " + str(self.cam.getPos())

        temp2 = self.loader.loadModel("models/Dice_Obj.obj")
        tex = self.loader.loadTexture('models/Dice_Base_Color.png')
        tex.setWrapV(Texture.WM_repeat)
        temp2.setTexture(tex, 2)
        temp2.reparentTo(self.cam)
        temp2.setScale(1, 1, 1)
        temp2.setPos(0, METER/2, 0)
        positiontemp = temp2.getPos(self.render)
        quattemp = temp2.getQuat(self.render)
        temp2.reparentTo(self.render)
        temp2.setPos(positiontemp)
        temp2.setQuat(quattemp)
        print "Temp object vs camera = " + str(temp2.getPos())

    def defineKeys(self):
        self.accept('escape', sys.exit)
        self.accept('1', self.startSlam)
        self.accept('2', self.startCalibration)
        self.accept('3', self.endCalibration)
        self.accept('4', self.verifyVirtualObject)
        self.accept('5', self.initHands)
        self.accept('6', self.detect_object)
        self.accept('7', self.activeAr)
        self.accept('8', self.detachObjetct)
        self.accept('9', self.set_plane)
        self.accept('a', self.showpoints)

    def generateText(self):
        self.onekeyText = genLabelText("ESC: Sair", 1, self)
        self.onekeyText = genLabelText("[1] - Start SLAM", 2, self)
        self.onekeyText = genLabelText("[2] - Start calibration", 3, self)
        self.onekeyText = genLabelText("[3] - End calibration", 4, self)
        self.onekeyText = genLabelText("[4] - Spawn ball in front of camera", 5, self)
        self.onekeyText = genLabelText("[5] - Activate GanHands", 6, self)
        self.onekeyText = genLabelText("[6] - Detect Object", 7, self)
        self.onekeyText = genLabelText("[7] - CAM POSITION", 8, self)
        self.onekeyText = genLabelText("[8] - Detach object", 9, self)
        self.onekeyText = genLabelText("[9] - Set plane", 10, self)
        self.onekeyText = genLabelText("[a] - Mostra pontos plano", 11, self)
