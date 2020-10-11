import sys
from direct.actor.Actor import Actor
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import loadPrcFileData, CardMaker, MovieTexture, Filename, Point2, TextNode, CollisionTraverser, \
    CollisionHandlerQueue, CollisionHandlerPusher, CollisionNode, CollisionCapsule, BitMask32, LVecBase3f, LQuaternion, \
    CollisionSphere
from direct.showbase.ShowBase import ShowBase
from panda3d.vision import WebcamVideo, ARToolKit
from direct.task import Task
from time import sleep
import gltf

loadPrcFileData("", "textures-power-2 none")  #the webcam feed can not be made into a power of two texture
loadPrcFileData("", "show-frame-rate-meter 1") #show fps
loadPrcFileData("", "sync-video 0") #turn off v-sync
loadPrcFileData("", "auto-flip 1") #usualy the drawn texture lags a bit behind the calculted positions. this is a try to reduce the lag.

positionArray = []
globalCounter = 0

ganPositionArray = []
globalGanCounter = 0
actualGanJoint = 0

def genLabelText(text, i, self):
    return OnscreenText(text=text, parent=self.a2dTopLeft, scale=.06,
                        pos=(0.06, -.08 * i), fg=(1, 1, 1, 1),
                        shadow=(0, 0, 0, .5), align=TextNode.ALeft)


class ARtest(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        gltf.patch_loader(self.loader)
        self.disable_mouse()

        self.cTrav = CollisionTraverser()

        self.cHandler = CollisionHandlerQueue()

        self.pusher = CollisionHandlerPusher()

        self.generateText()

        self.defineKeys()

        self.readFile()

        self.fillArray()

        self.fillGanArray()

        self.title = OnscreenText(text="Simulação do TCC",
                                  fg=(1, 1, 1, 1), parent=self.a2dBottomRight,
                                  align=TextNode.ARight, pos=(-0.1, 0.1),
                                  shadow=(0, 0, 0, .5), scale=.08)

        self.hand = Actor("models/Simple_Hand_AfterApply.gltf")
        self.hand.reparentTo(self.render)

        self.hand.setPos(0, 5, 0)

        self.loadHandJoints()

        self.allfingers = {  # --> Dictionary with all joints
            'T2': self.t2Thumb,
            'T1': self.t1Thumb,
            'T0': self.t0Thumb,
            'I2': self.i2IndexFinger,
            'I1': self.i1IndexFinger,
            'I0': self.i0IndexFinger,
            'M2': self.m2MiddleFinger,
            'M1': self.m1MiddleFinger,
            'M0': self.m0MiddleFinger,
            'R2': self.r2RingFinger,
            'R1': self.r1RingFinger,
            'R0': self.r0RingFinger,
            'L2': self.l2LittleFinger,
            'L1': self.l1LittleFinger,
            'L0': self.l0LittleFinger
        }

        self.define_fingers_collision()

        self.taskMgr.add(self.setHandPosition, "HandTracking")

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
        self.addObject()

        # updating the models positions each frame.
        sleep(1)  # some webcams are quite slow to start up so we add some safety
        self.taskMgr.add(self.updatePatterns, "update-patterns")

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
        print("Posição do objeto agora: " + str(self.axis.getPos()))

    def updatePatterns(self, task):
        self.ar.analyze(self.tex, True)
        return Task.cont

    def readFile(self):
        file = open("Trajetoria.txt", "r")
        self.txtLines = file.readlines()
        file.close()

        filegan = open("coordenadas.txt", "r")
        self.ganTxtLines = filegan.readlines()
        filegan.close()

    def callBackFunction(self):
        self.setGanNodes()
        #self.taskMgr.add(self.refreshCameraPosition, "refresh-camera-position")
        self.taskMgr.add(self.setGanNodesPosition, "set-gan-nodes-position")

    def setGanNodesPosition(self, task):
        global globalGanCounter
        global ganPositionArray
        global actualGanJoint

        if(globalGanCounter < 5866):
            self.ganNodes["Node{0}".format(actualGanJoint)].setPos(ganPositionArray[globalGanCounter])
            #self.ganNodes["Node{0}".format(actualGanJoint)].reparentTo(self.render)
            #self.ganNodes["Node{0}".format(actualGanJoint)].show()
            globalGanCounter += 1
            actualGanJoint += 1
            if(actualGanJoint == 21):
                actualGanJoint = 0

        sleep(0.033)#Wait until next iteration

        return Task.cont

    def setGanNodes(self):
        self.ganNodes = {}

        for i in range(21):
            cNode = CollisionNode("GanNode" + str(i))
            cNode.addSolid(CollisionSphere(0, 0, 0, 0.02))
            self.ganNodes["Node{0}".format(i)] = cNode
            self.ganNodes["Node{0}".format(actualGanJoint)].reparentTo(self.render)
            self.ganNodes["Node{0}".format(actualGanJoint)].show()

    def fillGanArray(self):
        global ganPositionArray

        contador = 0
        x = 0
        y = 0
        z = 0

        for line in self.ganTxtLines:
            if (contador % 5 == 2):
                contador += 1
                continue
            splitedString = line.split()
            x = float(splitedString[0]) / 100
            y = float(splitedString[2]) / 100
            z = float(splitedString[1]) / 100
            vector3f = LVecBase3f(x, y, z)
            ganPositionArray.append(vector3f)
            contador += 1

    def refreshCameraPosition(self, task):
        global globalCounter
        global positionArray

        if(globalCounter <= 816):
            quaternion = LQuaternion(positionArray[globalCounter][1][0], positionArray[globalCounter][1][1],
                                     positionArray[globalCounter][1][2], positionArray[globalCounter][1][3])
            self.cam.setPosQuat(positionArray[globalCounter][0], quaternion)
            globalCounter += 1

        sleep(0.033) #Wait until next iteration

        return Task.cont

    def fillArray(self):
        global positionArray

        contador = 0
        x = 0
        y = 0
        z = 0
        qx = 0
        qy = 0
        qz = 0
        qw = 0
        for line in self.txtLines:
            splitedString = line.split()
            if (contador == 0):
                x = float(splitedString[1]) * 10
                y = float(splitedString[2]) * 10
                z = float(splitedString[3]) * 10
            elif (contador == 1):
                qx = float(splitedString[0])
                qy = float(splitedString[1])
                qz = float(splitedString[2])
                qw = float(splitedString[3])
            contador += 1
            if (contador > 1):
                vector3f = LVecBase3f(x, y, z)
                quaternion = LQuaternion(qw, qz, qy, qx)
                cameraPos = [vector3f, quaternion]
                positionArray.append(cameraPos)
                contador = 0

    def loadHandJoints(self):
        # Joints do dedo mindinho
        self.l2LittleFinger = self.hand.controlJoint(None, 'modelRoot', 'L2')
        self.l1LittleFinger = self.hand.controlJoint(None, 'modelRoot', 'L1')
        self.l0LittleFinger = self.hand.controlJoint(None, 'modelRoot', 'L0')

        # Joints do dedo anelar
        self.r2RingFinger = self.hand.controlJoint(None, 'modelRoot', 'R2')
        self.r1RingFinger = self.hand.controlJoint(None, 'modelRoot', 'R1')
        self.r0RingFinger = self.hand.controlJoint(None, 'modelRoot', 'R0')

        # Joints do dedo do meio
        self.m2MiddleFinger = self.hand.controlJoint(None, 'modelRoot', 'M2')
        self.m1MiddleFinger = self.hand.controlJoint(None, 'modelRoot', 'M1')
        self.m0MiddleFinger = self.hand.controlJoint(None, 'modelRoot', 'M0')

        # Joints do dedo indicador
        self.i2IndexFinger = self.hand.controlJoint(None, 'modelRoot', 'I2')
        self.i1IndexFinger = self.hand.controlJoint(None, 'modelRoot', 'I1')
        self.i0IndexFinger = self.hand.controlJoint(None, 'modelRoot', 'I0')

        # Joints do dedão da mão
        self.t2Thumb = self.hand.controlJoint(None, 'modelRoot', 'T2')
        self.t1Thumb = self.hand.controlJoint(None, 'modelRoot', 'T1')
        self.t0Thumb = self.hand.controlJoint(None, 'modelRoot', 'T0')

    def define_capsule_collision(self, finger):
        connected_finger = finger
        nconnected_finger = int(finger[1]) - 1
        if nconnected_finger >= 0:
            connected_finger = finger[0] + str(nconnected_finger)

        cNode = CollisionNode("Collision" + finger)
        cNode.addSolid(CollisionCapsule((self.allfingers[finger].getY() - self.allfingers[connected_finger].getY())*0.25,
                             (self.allfingers[finger].getX() - self.allfingers[connected_finger].getX())*0.25,
                             (self.allfingers[finger].getZ() - self.allfingers[connected_finger].getZ())*0.25,
                             0, 0, 0, 0.02))
        c_armature = self.allfingers[finger].attachNewNode(cNode)
        c_armature.reparentTo(self.hand.exposeJoint(None, 'modelRoot', finger))
        c_armature.show()

    def define_fingers_collision(self):
        # finger radius 0.02
        for finger in self.allfingers:
            self.define_capsule_collision(finger)

    def defineKeys(self):
        self.accept('escape', sys.exit)
        self.accept('1', self.changePerspective, [-60, -60])
        self.accept('2', self.changePerspective, [-60, 60])
        self.accept('3', self.moveFingers)
        self.accept('4', self.resetPerspective)
        self.accept('5', self.resetFinger)
        self.accept('6', self.setHandDepth, [0.1])
        self.accept('7', self.setHandDepth, [-0.1])
        self.accept('8', self.resetHandPosition)
        self.accept('9', self.detachObjetct)
        self.accept('0', self.callBackFunction)

    def generateText(self):
        self.onekeyText = genLabelText("ESC: Sair", 1, self)
        self.onekeyText = genLabelText("[1]: Muda a Perpectiva da mão para o primeiro modo", 2, self)
        self.onekeyText = genLabelText("[2]: Muda a Perspectiva da mão para o segundo modo", 3, self)
        self.onekeyText = genLabelText("[3]: Mexe os dedos", 4, self)
        self.onekeyText = genLabelText("[4]: Volta a perspectiva da mão para o formato original", 5, self)
        self.onekeyText = genLabelText("[5]: Volta os dedos para a posição inicial", 6, self)
        self.onekeyText = genLabelText("[6]: Muda a profundidade da mão positivamente", 7, self)
        self.onekeyText = genLabelText("[7]: Muda a profundidade da mão negativamente", 8, self)
        self.onekeyText = genLabelText("[8]: Reseta a posição da mão", 9, self)
        self.onekeyText = genLabelText("[9]: Detach do objeto", 10, self)
        self.onekeyText = genLabelText("[0]: Muda as coordenadas da câmera de acordo com o SLAM", 11, self)

    def setHandPosition(self, task):
        if self.mouseWatcherNode.hasMouse():
            mousePosition = self.mouseWatcherNode.getMouse()
            self.hand.setX(mousePosition.getX() * 2)
            self.hand.setZ(mousePosition.getY() * 1.5)
            # print(self.hand.getPos())
        return Task.cont

    def setHandDepth(self, value):
        self.hand.setY(self.hand.getY() + value)

    def resetHandPosition(self):
        self.hand.setPos(0, 5, 0)

    def changePerspective(self, firstAngle, secondAngle):
        # Muda em Y e Z
        self.hand.setP(firstAngle)
        # Muda em X e Z
        self.hand.setR(secondAngle)
        # Muda em X e Y
        # self.hand.setH(60)

    def resetPerspective(self):
        self.hand.setP(0)
        self.hand.setR(0)

    def moveFingers(self):
        self.moveLittleFinger()
        self.moveRingFinger()
        self.moveMiddleFinger()
        self.moveIndexFinger()
        self.moveThumb()

    def moveLittleFinger(self):
        self.l0LittleFinger.setP(-20)
        self.l1LittleFinger.setP(-40)
        self.l2LittleFinger.setP(-30)

    def moveRingFinger(self):
        self.r0RingFinger.setP(-20)
        self.r1RingFinger.setP(-40)
        self.r2RingFinger.setP(-30)

    def moveMiddleFinger(self):
        self.m0MiddleFinger.setP(-20)
        self.m1MiddleFinger.setP(-40)
        self.m2MiddleFinger.setP(-30)

    def moveIndexFinger(self):
        self.i0IndexFinger.setP(-20)
        self.i1IndexFinger.setP(-40)
        self.i2IndexFinger.setP(-30)

    def moveThumb(self):
        self.t0Thumb.setP(-20)
        self.t1Thumb.setR(40)
        self.t2Thumb.setP(-30)
        self.t2Thumb.setR(40)

    def resetFinger(self):
        self.l0LittleFinger.setP(0)
        self.l1LittleFinger.setP(0)
        self.l2LittleFinger.setP(0)

        self.r0RingFinger.setP(0)
        self.r1RingFinger.setP(0)
        self.r2RingFinger.setP(0)

        self.m0MiddleFinger.setP(0)
        self.m1MiddleFinger.setP(0)
        self.m2MiddleFinger.setP(0)

        self.i0IndexFinger.setP(0)
        self.i1IndexFinger.setP(0)
        self.i2IndexFinger.setP(0)

        self.t0Thumb.setP(0)
        self.t1Thumb.setR(0)
        self.t2Thumb.setP(0)
        self.t2Thumb.setR(0)


demo = ARtest()
demo.run()