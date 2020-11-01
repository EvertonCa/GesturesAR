import sys
from Queue import Queue
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import loadPrcFileData, CardMaker, MovieTexture, Filename, Point2, TextNode, CollisionTraverser, \
    CollisionHandlerQueue, CollisionHandlerPusher, CollisionNode, BitMask32, LVecBase3f, LQuaternion, \
    CollisionSphere, NodePath, PStatClient, Texture, CollisionBox, LPoint3f, LVecBase3, CollisionPolygon
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

objectsize = [[0.30, 0.306640625, 0.26432291666666666666666666666667], [0.30, 0.2197265625, 0.375], [0.30, 0.228515625, 0.19661458333333333333333333333333], [0.40, 0.6328125, 58072916666666666666666666666667], [0.40, 0.384765625, 0.16015625]]
proportion_pixel2cm = [0.384765625, 0.185]

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
                a = float(xt)
                b = float(yt)
                c = float(zt)
                x = -(a / 1000)
                y = (c / 100)
                z = (b / 1000)
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
        p = Popen(['python3.7', 'PandaMarker.py'])
        while not os.path.exists('Marker/Marker.patt'):
            print "esperando..."
        self.addObject()

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
        fist_list = list()
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
                    if i == 0 or i == 2 or i == 5 or i == 17:
                        fist_list.append(calibratedVector3f)

                    #if i == 4 or i == 20 or i == 12:
                        #print("Coodenadas Nodo" + str(i) + "" + str(self.ganNodes["Node" + str(i)].getPos()) + "\n")

                if self.palm is not None:
                    self.palm.removeNode()
                cNode = CollisionNode("PalmNode")
                cNode.addSolid(CollisionPolygon(fist_list[0], fist_list[1], fist_list[2], fist_list[3]))

                nodePath = NodePath("NodePathpalm")
                self.palm = nodePath.attachNewNode(cNode)
                self.palm.reparentTo(self.cam)
                self.palm.show()

                #print("Coordenadas Camera: " + str(self.cam.getPos()) + "\n")
        return task.cont

    def setGanNodes(self):
        for i in range(21):
            cNode = CollisionNode("GanNode" + str(i))
            cNode.addSolid(CollisionSphere(0, 0, 0, 0.005))
            nodePath = NodePath("NodePath{0}".format(i))
            self.temp = self.render.attachNewNode("temp")
            self.temp.setPos(self.cam.getPos())
            self.ganNodes["Node{0}".format(i)] = nodePath.attachNewNode(cNode)
            self.ganNodes["Node{0}".format(i)].reparentTo(self.temp)

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
                self.dice = self.loader.loadModel("models/Dice_Obj.obj")
                tex = self.loader.loadTexture('models/Dice_Base_Color.png')
                tex.setWrapV(Texture.WM_repeat)
                self.dice.setTexture(tex, 2)

                self.dice.reparentTo(self.render)
                self.dice.setScale(2, 2, 2)
                x = self.cam.getX()
                y = self.cam.getY()
                z = self.cam.getZ()

                if self.surface_box is not None:
                    self.dice.setPos(self.surface_box.getPos())
                    self.dice.setZ(self.surface_box.getZ() + (self.surface_box.getSz() + self.dice.getSz()) / 2)
                #elif objectDetect is True:
                else:
                    self.dice.setPos(x, y + 3.5, z)

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
                print "Object added at x = " + str(self.dice.getX()) + " y = " + str(self.dice.getY()) + " z = " + str(self.dice.getX())

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
        object_distance = objectsize[label_number][0]*objectsize[label_number][2]/float(yolo_parameters[3])

        distancia_do_centro = (float(yolo_parameters[2]) - 0.5)
        x = proportion_pixel2cm[1] * distancia_do_centro / proportion_pixel2cm[0]

        distancia_do_centro = (float(yolo_parameters[3]) - 0.5)
        y = proportion_pixel2cm[1] * distancia_do_centro / proportion_pixel2cm[0]

        temp = self.loader.loadModel("models/Dice_Obj.obj")
        tex = self.loader.loadTexture('models/Dice_Base_Color.png')
        tex.setWrapV(Texture.WM_repeat)
        temp.setTexture(tex, 2)
        temp.reparentTo(self.cam)
        temp.setScale(0.15, 0.15, 0.15)
        temp.setPos(x, object_distance, y)

        worldPosition = temp.getPos(self.render)
        worldQuat = temp.getQuat(self.render)

        temp.reparentTo(self.render)
        temp.setPos(worldPosition)
        temp.setQuat(worldQuat)
        print "Cubo em " + str(temp.getPos())
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
        dx, dy, dz = 5, 5, 0.01

        print "Coordenadas Camera: " + str(self.cam.getPos()) + "\n"

        self.surface_box = self.loader.loadModel('models/cube.obj')
        self.surface_box.reparentTo(self.render)
        tex = self.loader.loadTexture('models/iron05.jpg')
        tex.setWrapU(Texture.WM_repeat)
        self.surface_box.setTexture(tex, 2)
        self.surface_box.setPos(x, y, z - dz)
        self.surface_box.setScale(dx, dy, dz)
        print "Quaternio do plano" + str(self.surface_box.getQuat())
        #self.surface_box.setQuat(self.cam.getQuat())

        cNode = CollisionNode("SurfaceNode")
        cNode.addSolid(CollisionBox(LPoint3f(x, y, z - dz), dx, dy, dz))
        nodePath = NodePath("NodePath")
        self.collision_surface = nodePath.attachNewNode(cNode)
        self.collision_surface.reparentTo(self.render)

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

    def upDice(self):
        temp = self.temp.getY()
        self.temp.setY(temp + 1)
        self.imprime()
    def downDice(self):
        temp = self.temp.getY()
        self.temp.setY(temp - 1)
        self.imprime()
    def rightDice(self):
        temp = self.temp.getX()
        self.temp.setX(temp + 1)
        self.imprime()

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
        self.accept('w', self.upDice)
        self.accept('s', self.downDice)
        self.accept('d', self.rightDice)

    def generateText(self):
        self.onekeyText = genLabelText("ESC: Sair", 1, self)
        self.onekeyText = genLabelText("[1] - Start SLAM", 2, self)
        self.onekeyText = genLabelText("[2] - Start calibration", 3, self)
        self.onekeyText = genLabelText("[3] - End calibration", 4, self)
        self.onekeyText = genLabelText("[4] - Spawn ball in front of camera", 5, self)
        self.onekeyText = genLabelText("[5] - Activate GanHands", 6, self)
        self.onekeyText = genLabelText("[6] - Detect Object", 7, self)
        self.onekeyText = genLabelText("[7] - Active AR", 8, self)
        self.onekeyText = genLabelText("[8] - Detach object", 9, self)
        self.onekeyText = genLabelText("[9] - Set plane", 10, self)
        self.onekeyText = genLabelText("[a] - Mostra pontos plano", 11, self)
        self.onekeyText = genLabelText("[a] - Set plane", 12, self)
        self.onekeyText = genLabelText("[a] - Set plane", 13, self)
        self.onekeyText = genLabelText("[a] - Set plane", 14, self)
