import sys
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import loadPrcFileData, CardMaker, MovieTexture, Filename, Point2, TextNode, CollisionTraverser, \
    CollisionHandlerQueue, CollisionHandlerPusher, CollisionNode, BitMask32, LVecBase3f, LQuaternion, \
    CollisionSphere, NodePath
from direct.showbase.ShowBase import ShowBase
from panda3d.vision import WebcamVideo, ARToolKit
from direct.task import Task
from time import sleep

loadPrcFileData("", "textures-power-2 none")  #the webcam feed can not be made into a power of two texture
loadPrcFileData("", "show-frame-rate-meter 1") #show fps
loadPrcFileData("", "sync-video 0") #turn off v-sync
loadPrcFileData("", "auto-flip 1") #usualy the drawn texture lags a bit behind the calculted positions. this is a try to reduce the lag.

canUpdateSlam = False

positionArray = []
globalCounter = 0

temp_ganPositionArray = []
ganPositionArray0 = []
ganPositionArray1 = []
ganPositionArray2 = []
ganPositionArray3 = []
ganPositionArray4 = []
ganPositionArray5 = []
ganPositionArray6 = []
ganPositionArray7 = []
ganPositionArray8 = []
ganPositionArray9 = []
ganPositionArray10 = []
ganPositionArray11 = []
ganPositionArray12 = []
ganPositionArray13 = []
ganPositionArray14 = []
ganPositionArray15 = []
ganPositionArray16 = []
ganPositionArray17 = []
ganPositionArray18 = []
ganPositionArray19 = []
ganPositionArray20 = []

globalGanCounter = 0
actualGanJoint = 0

def genLabelText(text, i, self):
    return OnscreenText(text=text, parent=self.a2dTopLeft, scale=.04,
                        pos=(0.06, -.08 * i), fg=(1, 1, 1, 1),
                        shadow=(0, 0, 0, .5), align=TextNode.ALeft)

def updateSlam(text):
    global positionArray
    global canUpdateSlam

    if len(text) > 0:

        splitedString = text.split()
        x = float(splitedString[1]) * 10
        y = float(splitedString[2]) * 10
        z = float(splitedString[3]) * 10
        qx = float(splitedString[4])
        qy = float(splitedString[5])
        qz = float(splitedString[6])
        qw = float(splitedString[7])

        vector3f = LVecBase3f(x, z, -y)
        quaternion = LQuaternion(qw, qx, qz, -qy)
        cameraPos = [vector3f, quaternion]
        positionArray = cameraPos
        canUpdateSlam = True



class ARScene(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.cTrav = CollisionTraverser()

        self.cHandler = CollisionHandlerQueue()

        self.pusher = CollisionHandlerPusher()

        self.generateText()

        self.defineKeys()

        # for x, option in enumerate(WebcamVideo.getOptions()):
        #     print(option, x)

        self.title = OnscreenText(text="TCC Simulation",
                                  fg=(1, 1, 1, 1), parent=self.a2dBottomRight,
                                  align=TextNode.ARight, pos=(-0.1, 0.1),
                                  shadow=(0, 0, 0, .5), scale=.08)

        #Windows WebCam
        option = WebcamVideo.getOption(0)  # 0 here is default webcam, 1 would be second cam etc.
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

        # load a model to visualize the tracking
        #self.addObject()

        self.ball = self.loader.loadModel("models/ball")

        self.ball.reparentTo(self.render)

        self.ball.setScale(0.25, 0.25, 0.25)

        self.ball.setPos(0, 5, 0)

        # updating the models positions each frame.
        sleep(1)  # some webcams are quite slow to start up so we add some safety
        self.taskMgr.add(self.updatePatterns, "update-patterns")
        self.taskMgr.add(self.refreshCameraPosition, "refresh-camera-position")


    def addObject(self):
        self.axis = self.loader.loadModel("models/ball")
        self.axis.reparentTo(self.render)
        self.axis.setScale(0.5, 0.5, 0.5)

        self.ballSphere = self.axis.find("**/ball")
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

    def callBackFunction(self):
        self.setGanNodes()
        #self.taskMgr.add(self.setGanNodesPosition, "set-gan-nodes-position")

    def setGanNodesPosition(self, task):
        global globalGanCounter
        global temp_ganPositionArray
        global ganPositionArray0
        global ganPositionArray1
        global ganPositionArray2
        global ganPositionArray3
        global ganPositionArray4
        global ganPositionArray5
        global ganPositionArray6
        global ganPositionArray7
        global ganPositionArray8
        global ganPositionArray9
        global ganPositionArray10
        global ganPositionArray11
        global ganPositionArray12
        global ganPositionArray13
        global ganPositionArray14
        global ganPositionArray15
        global ganPositionArray16
        global ganPositionArray17
        global ganPositionArray18
        global ganPositionArray19
        global ganPositionArray20
        #global actualGanJoint

        if(globalGanCounter < 279):
            #self.ganNodes["Node{0}".format(actualGanJoint)].setPos(temp_ganPositionArray[globalGanCounter])
            self.ganNodes["Node0"].setPos(ganPositionArray0[globalGanCounter])
            self.ganNodes["Node1"].setPos(ganPositionArray1[globalGanCounter])
            self.ganNodes["Node2"].setPos(ganPositionArray2[globalGanCounter])
            self.ganNodes["Node3"].setPos(ganPositionArray3[globalGanCounter])
            self.ganNodes["Node4"].setPos(ganPositionArray4[globalGanCounter])
            self.ganNodes["Node5"].setPos(ganPositionArray5[globalGanCounter])
            self.ganNodes["Node6"].setPos(ganPositionArray6[globalGanCounter])
            self.ganNodes["Node7"].setPos(ganPositionArray7[globalGanCounter])
            self.ganNodes["Node8"].setPos(ganPositionArray8[globalGanCounter])
            self.ganNodes["Node9"].setPos(ganPositionArray9[globalGanCounter])
            self.ganNodes["Node10"].setPos(ganPositionArray10[globalGanCounter])
            self.ganNodes["Node11"].setPos(ganPositionArray11[globalGanCounter])
            self.ganNodes["Node12"].setPos(ganPositionArray12[globalGanCounter])
            self.ganNodes["Node13"].setPos(ganPositionArray13[globalGanCounter])
            self.ganNodes["Node14"].setPos(ganPositionArray14[globalGanCounter])
            self.ganNodes["Node15"].setPos(ganPositionArray15[globalGanCounter])
            self.ganNodes["Node16"].setPos(ganPositionArray16[globalGanCounter])
            self.ganNodes["Node17"].setPos(ganPositionArray17[globalGanCounter])
            self.ganNodes["Node18"].setPos(ganPositionArray18[globalGanCounter])
            self.ganNodes["Node19"].setPos(ganPositionArray19[globalGanCounter])
            self.ganNodes["Node20"].setPos(ganPositionArray20[globalGanCounter])

            self.ganNodes["Node0"].show()
            self.ganNodes["Node1"].show()
            self.ganNodes["Node2"].show()
            self.ganNodes["Node3"].show()
            self.ganNodes["Node4"].show()
            self.ganNodes["Node5"].show()
            self.ganNodes["Node6"].show()
            self.ganNodes["Node7"].show()
            self.ganNodes["Node8"].show()
            self.ganNodes["Node9"].show()
            self.ganNodes["Node10"].show()
            self.ganNodes["Node11"].show()
            self.ganNodes["Node12"].show()
            self.ganNodes["Node13"].show()
            self.ganNodes["Node14"].show()
            self.ganNodes["Node15"].show()
            self.ganNodes["Node16"].show()
            self.ganNodes["Node17"].show()
            self.ganNodes["Node18"].show()
            self.ganNodes["Node19"].show()
            self.ganNodes["Node20"].show()

            print(self.ganNodes["Node0"].getPos())
            print(self.ganNodes["Node8"].getPos())

            globalGanCounter += 1

        sleep(0.033)#Wait until next iteration

        return Task.cont

    def setGanNodes(self):
        self.ganNodes = {}

        for i in range(21):
            cNode = CollisionNode("GanNode" + str(i))
            cNode.addSolid(CollisionSphere(0, 0, 0, 0.02))
            nodePath = NodePath("NodePath{0}".format(i))
            self.ganNodes["Node{0}".format(i)] = nodePath.attachNewNode(cNode)
            self.ganNodes["Node{0}".format(i)].reparentTo(self.render)
            #self.ganNodes["Node{0}".format(actualGanJoint)].show()

    def fillGanArray(self):
        #global temp_ganPositionArray
        global ganPositionArray0
        global ganPositionArray1
        global ganPositionArray2
        global ganPositionArray3
        global ganPositionArray4
        global ganPositionArray5
        global ganPositionArray6
        global ganPositionArray7
        global ganPositionArray8
        global ganPositionArray9
        global ganPositionArray10
        global ganPositionArray11
        global ganPositionArray12
        global ganPositionArray13
        global ganPositionArray14
        global ganPositionArray15
        global ganPositionArray16
        global ganPositionArray17
        global ganPositionArray18
        global ganPositionArray19
        global ganPositionArray20

        contador = 0
        x = 0
        y = 0
        z = 0

        for i in range(len(self.ganTxtLines)):
            if(i % 5 == 2):
                continue
            splitedString = self.ganTxtLines[i].split()
            x = (float(splitedString[0]) / 200) * -1
            y = float(splitedString[2]) / 50
            z = float(splitedString[1]) / 200
            vector3f = LVecBase3f(x, y, z)
            if (contador == 0):
                ganPositionArray0.append(vector3f)
            elif (contador == 1):
                ganPositionArray1.append(vector3f)
            elif (contador == 2):
                ganPositionArray2.append(vector3f)
            elif (contador == 3):
                ganPositionArray3.append(vector3f)
            elif (contador == 4):
                ganPositionArray4.append(vector3f)
            elif (contador == 5):
                ganPositionArray5.append(vector3f)
            elif (contador == 6):
                ganPositionArray6.append(vector3f)
            elif (contador == 7):
                ganPositionArray7.append(vector3f)
            elif (contador == 8):
                ganPositionArray8.append(vector3f)
            elif (contador == 9):
                ganPositionArray9.append(vector3f)
            elif (contador == 10):
                ganPositionArray10.append(vector3f)
            elif (contador == 11):
                ganPositionArray11.append(vector3f)
            elif (contador == 12):
                ganPositionArray12.append(vector3f)
            elif (contador == 13):
                ganPositionArray13.append(vector3f)
            elif (contador == 14):
                ganPositionArray14.append(vector3f)
            elif (contador == 15):
                ganPositionArray15.append(vector3f)
            elif (contador == 16):
                ganPositionArray16.append(vector3f)
            elif (contador == 17):
                ganPositionArray17.append(vector3f)
            elif (contador == 18):
                ganPositionArray18.append(vector3f)
            elif (contador == 19):
                ganPositionArray19.append(vector3f)
            elif (contador == 20):
                ganPositionArray20.append(vector3f)

            contador += 1
            if (contador == 21):
                contador = 0


    def refreshCameraPosition(self, task):
        global canUpdateSlam
        global positionArray

        if(canUpdateSlam):
            quaternion = LQuaternion(positionArray[1][0], positionArray[1][1],
                                     positionArray[1][2], positionArray[1][3])
            self.cam.setPosQuat(positionArray[0], quaternion)
            canUpdateSlam = False

        #sleep(0.033) #Wait until next iteration

        return Task.cont


    def defineKeys(self):
        self.accept('escape', sys.exit)
        self.accept('1', self.detachObjetct)
        self.accept('2', self.callBackFunction)

    def generateText(self):
        self.onekeyText = genLabelText("ESC: Sair", 1, self)
        self.onekeyText = genLabelText("[1] - Object detach", 2, self)
        self.onekeyText = genLabelText("[2] - Call callback function", 3, self)