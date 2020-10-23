import sys
from Queue import Queue
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import loadPrcFileData, CardMaker, MovieTexture, Filename, Point2, TextNode, CollisionTraverser, \
    CollisionHandlerQueue, CollisionHandlerPusher, CollisionNode, BitMask32, LVecBase3f, LQuaternion, \
    CollisionSphere, NodePath, PStatClient
from direct.showbase.ShowBase import ShowBase
from panda3d.vision import WebcamVideo, ARToolKit
from direct.task import Task
from time import sleep
import threading
from DistanceCalibrator import DistanceCalibrator

loadPrcFileData("", "textures-power-2 none")  #the webcam feed can not be made into a power of two texture
loadPrcFileData("", "show-frame-rate-meter 1") #show fps
loadPrcFileData("", "sync-video 0") #turn off v-sync
loadPrcFileData("", "auto-flip 1") #usualy the drawn texture lags a bit behind the calculted positions. this is a try to reduce the lag.

canUpdateHands = False
isObjectCreated = False

positionArray = []
globalCounter = 0

ganPositionArray = []

globalGanCounter = 0
actualGanJoint = 0

queueSlam = Queue()


def genLabelText(text, i, self):
    return OnscreenText(text=text, parent=self.a2dTopLeft, scale=.04,
                        pos=(0.06, -.08 * i), fg=(1, 1, 1, 1),
                        shadow=(0, 0, 0, .5), align=TextNode.ALeft)


def updateSlam(text):
    global positionArray
    global globalCounter
    global queueSlam

    if len(text) > 0:
        splitedString = text.split()
        globalCounter = int(splitedString[0])
        x = float(splitedString[1]) * 10
        y = float(splitedString[2]) * 10
        z = float(splitedString[3]) * 10
        qx = float(splitedString[4])
        qy = float(splitedString[5])
        qz = float(splitedString[6])
        qw = float(splitedString[7])
        vector3f = LVecBase3f(x, z, -y)
        quaternion = LQuaternion(qw, qx, qz, -qy)
        cameraPos = [vector3f, quaternion, int(splitedString[0])]
        positionArray = cameraPos
        queueSlam.put(cameraPos)


def updateHands(text):
    global ganPositionArray
    global canUpdateHands

    if canUpdateHands:
        ganPositionArray = []

        splitText = text.split('][')

        for i, line in enumerate(splitText):
            temp = line.replace('"', '').replace('[', '').replace(',', '').replace(';', '').replace(']', '').replace(
                '\n',
                '')
            if len(temp) > 2:
                x, y, z = temp.split(" ")
                a = float(x)
                b = float(y)
                c = float(z)
                x = (a / (-600))
                y = (c / 50)
                z = (b / 600)
                vector3f = LVecBase3f(x, y, z)
                ganPositionArray.append(vector3f)

        #canUpdateHands = True


class ARScene(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # PStatClient.connect()

        self.ball = None

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
        self.ar = ARToolKit.make(self.cam, Filename(self.mainDir, "ar/camera_para.dat"), 1)

        # variables for the system
        self.axis = self.loader.loadModel("models/ball")
        self.ballSphere = self.axis.find("**/ball")
        self.ganNodes = {}

        # updating the models positions each frame.
        sleep(1)  # some webcams are quite slow to start up so we add some safety
        #self.taskMgr.add(self.updatePatterns, "update-patterns")
        #self.taskMgr.add(self.refreshCameraPosition, "refresh-camera-position", sort= 0, priority=0)
        slam_thread = threading.Thread(target=self.refreshCameraPosition)
        slam_thread.start()
        #self.setGanNodes()
        #self.taskMgr.add(self.setGanNodesPosition, "set-gan-nodes-position")

    def addObject(self):
        self.axis.reparentTo(self.render)
        self.axis.setScale(0.5, 0.5, 0.5)
        self.ballSphere.node().setFromCollideMask(BitMask32.bit(1))
        self.ballSphere.node().setIntoCollideMask(BitMask32.allOff())
        self.ballSphere.show()

        self.cTrav.addCollider(self.ballSphere, self.pusher)

        self.pusher.addCollider(self.ballSphere, self.axis, self.drive.node())

        # attach the model to a pattern so it updates the model's position relative to the camera each time we call analyze()
        self.ar.attachPattern(Filename(self.mainDir, "ar/patt.kanji"), self.axis)
        #self.ar.attachPattern(Filename(self.mainDir, "ar/groot_720.patt"), self.axis)

    def detachObjetct(self):
        self.ar.detachPatterns()
        print("Object position now: " + str(self.axis.getPos()))

    def updatePatterns(self, task):
        self.ar.analyze(self.tex, True)
        return Task.cont

    def setGanNodesPosition(self, task):
        global ganPositionArray
        global canUpdateHands

        if canUpdateHands:
            for i in range(len(ganPositionArray)):
                #print (str(i) + " --> " + str(ganPositionArray[i]))
                self.ganNodes["Node" + str(i)].setPos(ganPositionArray[i])
                self.ganNodes["Node" + str(i)].show()
                #print (self.ganNodes["Node" + str(i)].getPos())

            #canUpdateHands = False
            #print ('\n\n\n')
        return Task.cont

    def setGanNodes(self):
        for i in range(21):
            cNode = CollisionNode("GanNode" + str(i))
            cNode.addSolid(CollisionSphere(0, 0, 0, 0.02))
            nodePath = NodePath("NodePath{0}".format(i))
            self.ganNodes["Node{0}".format(i)] = nodePath.attachNewNode(cNode)
            self.ganNodes["Node{0}".format(i)].reparentTo(self.render)

    def refreshCameraPosition(self):
        global positionArray
        global globalCounter
        global queueSlam

        while True:
            if not queueSlam.empty():
                array = queueSlam.get()
                if self.calibrator.ready:
                    temp2 = self.calibrator.convertSlamToWorld(array[0].getX(), array[0].getY(), array[0].getZ())
                    temp = LVecBase3f(temp2[0], temp2[1], temp2[2])
                    array[0] = temp

                quaternion = LQuaternion(array[1][0], array[1][1], array[1][2], array[1][3])
                self.cam.setPosQuat(array[0], quaternion)

            sleep(1000/30)

    def verifyVirtualObject(self):
        global isObjectCreated

        if self.calibrator.ready and not isObjectCreated:
            self.ball = self.loader.loadModel("models/ball")
            self.ball.reparentTo(self.render)
            self.ball.setScale(0.15, 0.15, 0.15)
            x = self.cam.getX()
            y = self.cam.getY()
            z = self.cam.getZ()
            self.ball.setPos(x, y + 2.0, z)

            self.ballSphere = self.ball.find("**/ball")
            self.ballSphere.node().setFromCollideMask(BitMask32.bit(1))
            self.ballSphere.node().setIntoCollideMask(BitMask32.allOff())
            self.ballSphere.show()

            self.cTrav.addCollider(self.ballSphere, self.pusher)

            self.pusher.addCollider(self.ballSphere, self.ball, self.drive.node())
            self.cTrav.showCollisions(self.render)

            isObjectCreated = True

    def startCalibration(self):
        x = self.cam.getX()
        y = self.cam.getY()
        z = self.cam.getZ()

        self.calibrator.setStart(x, y, z)

    def endCalibration(self):
        x = self.cam.getX()
        y = self.cam.getY()
        z = self.cam.getZ()

        self.calibrator.setEnd(x, y, z)

    def defineKeys(self):
        self.accept('escape', sys.exit)
        self.accept('1', self.detachObjetct)
        self.accept('2', self.startCalibration)
        self.accept('3', self.endCalibration)
        self.accept('4', self.verifyVirtualObject)

    def generateText(self):
        self.onekeyText = genLabelText("ESC: Sair", 1, self)
        self.onekeyText = genLabelText("[1] - Object detach", 2, self)
        self.onekeyText = genLabelText("[2] - Start calibration", 3, self)
        self.onekeyText = genLabelText("[3] - End calibration", 4, self)
        self.onekeyText = genLabelText("[4] - Spawn ball in front of camera", 5, self)
