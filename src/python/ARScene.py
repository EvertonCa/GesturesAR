import sys
from Queue import Queue
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import loadPrcFileData, CardMaker, MovieTexture, Point2, TextNode, CollisionTraverser, \
    CollisionHandlerPusher, CollisionNode, LVecBase3f, LQuaternion, CollisionSphere, NodePath, Texture, CollisionBox, \
    LPoint3f, CollisionTube, BitMask32
from direct.showbase.ShowBase import ShowBase
from panda3d.vision import WebcamVideo
from DistanceCalibrator import DistanceCalibrator
from HorizontalPlaneCorrection import send_factor_to_slam
from ObjectDetection import object_detection
from threading import Thread
import numpy as np
import time
from panda3d.core import AmbientLight, DirectionalLight, LVector3
from math import pi, sin
from direct.interval.FunctionInterval import Func, Wait
from direct.interval.LerpInterval import LerpFunc
from direct.interval.MetaInterval import Sequence, Parallel
from ObjectMeasurements import *

METER = 25.4

loadPrcFileData("", "textures-power-2 none")  #the webcam feed can not be made into a power of two texture
loadPrcFileData("", "sync-video 0") #turn off v-sync
loadPrcFileData("", "auto-flip 1") #usualy the drawn texture lags a bit behind the calculted positions. this is a try to reduce the lag.

canUpdateYOLO = True
canUpdatePlane = True
canUpdateHands = False
canUpdateSlam = False
isObjectCreated = False

calibrated = False

yoloBB = ""
plane = ""

queueSlam = Queue()
queueSlamCalibrated = Queue()
queueHands = Queue()


# handles the in screen text
def genLabelText(text, i, self):
    return OnscreenText(text=text, parent=self.a2dBottomLeft, scale=.04,
                        pos=(0.06, .08 * i), fg=(1, 1, 1, 1),
                        shadow=(0, 0, 0, .5), align=TextNode.ALeft)


# receives the YOLO coordinates and saves it in the correspondent global variable (It is called each frame)
def updateYOLO(text):
    global canUpdateYOLO
    global yoloBB

    if len(text) > 0:
        if canUpdateYOLO:
            yoloBB = text


# receives the SLAM plane coordinates and saves it in the correspondent global variable (It is called each frame)
def updatePlane(text):
    global canUpdatePlane
    global plane

    if len(text) > 0:
        if canUpdatePlane:
            plane = text


# receives the SLAM coordinates and saves it in the correspondent global variable (It is called each frame)
def updateSlam(text):
    global queueSlam
    global queueSlamCalibrated
    global calibrated

    if len(text) > 0:
        splitedString = text.split()
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
        if calibrated:
            queueSlamCalibrated.put(cameraPos)
        else:
            queueSlam.put(cameraPos)


# receives the GANHands coordinates and saves it in the correspondent global variable (It is called each frame)
def updateHands(text):
    global queueHands
    global canUpdateHands

    if canUpdateHands:
        splitText = text.split('][')

        for i, line in enumerate(splitText):
            temp = line.replace('"', '').replace('[', '').replace(',', '').replace(';', '').\
                replace(']', '').replace('\n', '')
            if len(temp) > 2:
                xt, yt, zt = temp.split(" ")
                a = float(xt)
                b = float(yt)
                c = float(zt)
                x = (-(a / 1000) * METER) - 8.0
                y = (c / 1000) * METER * 5.0
                z = ((b / 1000) * METER) + 5.0
                vector3f = LVecBase3f(x, y, z)
                queueHands.put(vector3f)


# Main class
class ARScene(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.label_yolo = {
            'Dualshock4': 0,
            'IamGroot': 1,
            'MiniCraque': 2,
            'PlayStation2': 3,
            'Carrinho': 4
        }

        self.calibrator = DistanceCalibrator()

        self.cTrav = CollisionTraverser()

        self.pusher = CollisionHandlerPusher()

        self.generateText()

        self.defineKeys()

        self.title = OnscreenText(text="TCC Simulation",
                                  fg=(1, 1, 1, 1), parent=self.a2dBottomRight,
                                  align=TextNode.ARight, pos=(-0.1, 0.1),
                                  shadow=(0, 0, 0, .5), scale=.07)

        #Windows WebCam
        option = WebcamVideo.getOption(296)  # 0 here is default webcam, 1 would be second cam etc.
        self.tex = MovieTexture(option)
        self.tex.setTexturesPower2(0)
        self.tex.setKeepRamImage(True)

        # create a card which shows the image captured by the webcam.
        cm = CardMaker("background-card")
        cm.setUvRange(Point2(0, 0), Point2(1, 1))
        cm.setFrame(-1, 1, -1, 1)
        card = self.render2d.attachNewNode(cm.generate())
        card.setTexture(self.tex)

        # set the rendering order manually to render the card-with the webcam-image behind the scene.
        self.cam.node().getDisplayRegion(0).setSort(20)

        # variables for the system
        self.axis = self.loader.loadModel("models/ball")
        self.ballSphere = self.axis.find("**/ball")

        self.pipeline = None
        self.pipelineHands = None
        self.setupLightsModels()
        self.modelandcollision = None
        self.ganNodes = {}
        self.setGanNodes()

        self.ganCollisions = {}
        self.cylinder = {}
        self.define_capsule_collision()
        self.define_cylinders()

        self.surface_box = None

        # starts task manager for the camera position
        self.taskMgr.add(self.refreshCameraPosition, "refresh-camera-position", sort=0, priority=0)

    # starts task manager for the hands coordinates
    def initHands(self):
        global canUpdateHands

        canUpdateHands = True
        self.taskMgr.add(self.setGanNodesPosition, "set-gan-nodes-position")

    # sets the position for each hand node
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

                    self.set_capsule_collision(i)
                    self.set_cylinder_position(i)

        return task.cont

    # sets the hand capsules collisions
    def set_capsule_collision(self, i):
        if i == 0:
            return
        elif i % 4 == 1:
            self.ganCollisions["Collision{0}".format(i)].node().modifySolid(0).setPointA(
                self.ganNodes["Node{0}".format(0)].getPos(self.cam) - self.ganNodes["Node{0}".format(i)].getPos(self.cam))
        else:
            self.ganCollisions["Collision{0}".format(i)].node().modifySolid(0).setPointA(
                self.ganNodes["Node{0}".format(i-1)].getPos(self.cam) - self.ganNodes["Node{0}".format(i)].getPos(self.cam))

        self.ganCollisions["Collision{0}".format(i)].show()

    # sets the hand cylinders positions
    def set_cylinder_position(self, i):
        if i == 0:
            return
        elif i % 4 == 1:
            self.cylinder["Cylinder{0}".format(i)].setPos(
                (self.ganNodes["Node{0}".format(0)].getPos() - self.ganNodes["Node{0}".format(i)].getPos()) / 2)
            p1 = (self.ganNodes["Node{0}".format(0)].getX(), self.ganNodes["Node{0}".format(0)].getY(),
                  self.ganNodes["Node{0}".format(0)].getZ())
        else:
            self.cylinder["Cylinder{0}".format(i)].setPos(
                (self.ganNodes["Node{0}".format(i - 1)].getPos() - self.ganNodes["Node{0}".format(i)].getPos()) / 2)
            p1 = (self.ganNodes["Node{0}".format(i - 1)].getX(), self.ganNodes["Node{0}".format(i - 1)].getY(),
                  self.ganNodes["Node{0}".format(i - 1)].getZ())

        p2 = (self.ganNodes["Node{0}".format(i)].getX(), self.ganNodes["Node{0}".format(i)].getY(),
              self.ganNodes["Node{0}".format(i)].getZ())
        eudi = self.euclidean_distance(p1, p2)
        self.cylinder["Cylinder{0}".format(i)].setScale((0.20, 0.20, eudi))
        self.cylinder["Cylinder{0}".format(i)].lookAt(self.ganNodes["Node{0}".format(i)])
        self.cylinder["Cylinder{0}".format(i)].setP(self.cylinder["Cylinder{0}".format(i)].getP() + 90)

    # returns the euclidean distance between start and end
    def euclidean_distance(self, start, end):
        eudi = np.sqrt((np.power(end[0] - start[0], 2)) + (np.power(end[1] - start[1], 2)) + (
            np.power(end[2] - start[2], 2)))
        return eudi

    # defines the hand capsules collisions
    def define_capsule_collision(self):
        for i in range(1, 21):
            cNode = CollisionNode("Collision" + str(i))
            cNode.addSolid(CollisionTube(0, 0, 0, 0, 0, 0, 0.1))
            nodePath = NodePath("NodePathCollision{0}".format(i))
            self.ganCollisions["Collision{0}".format(i)] = nodePath.attachNewNode(cNode)
            self.ganCollisions["Collision{0}".format(i)].reparentTo(self.ganNodes["Node{0}".format(i)])

    # defines the hand cylinders
    def define_cylinders(self):
        for i in range(1, 21):
            self.cylinder["Cylinder{0}".format(i)] = self.loader.loadModel("models/cylinder")
            self.cylinder["Cylinder{0}".format(i)].reparentTo(self.ganNodes["Node{0}".format(i)])
            self.cylinder["Cylinder{0}".format(i)].setScale(0.25, 0.25, 0.25)
            self.cylinder["Cylinder{0}".format(i)].setPos(0, 0, 0)

    # sets the hand nodes
    def setGanNodes(self):
        for i in range(21):
            cNode = CollisionNode("GanNode" + str(i))
            cNode.addSolid(CollisionSphere(0, 0, 0, 0.1))
            nodePath = NodePath("NodePath{0}".format(i))
            self.ganNodes["Node{0}".format(i)] = nodePath.attachNewNode(cNode)
            self.ganNodes["Node{0}".format(i)].reparentTo(self.pipelineHands)

    # refreshes the camera position based on the SLAM coordinates
    def refreshCameraPosition(self, task):
        global queueSlam
        global calibrated
        global queueSlamCalibrated

        if calibrated:
            if not queueSlamCalibrated.empty():
                array = queueSlamCalibrated.get()
                temp2 = self.calibrator.convertSlamToWorld(array[0].getX(), array[0].getY(), array[0].getZ())
                temp = LVecBase3f(temp2[0], temp2[1], temp2[2])
                array[0] = temp
                quaternion = LQuaternion(array[1][0], array[1][1], array[1][2], array[1][3])
                self.cam.setPosQuat(array[0], quaternion)
        else:
            if not queueSlam.empty():
                array = queueSlam.get()
                quaternion = LQuaternion(array[1][0], array[1][1], array[1][2], array[1][3])
                self.cam.setPosQuat(array[0], quaternion)
        return task.cont

    # spawns the 3D object
    def spawnObject(self):
        global isObjectCreated
        global objectInitialPosition

        if self.calibrator.ready:
            if not isObjectCreated:
                x = self.cam.getX(self.render)
                y = self.cam.getY(self.render)
                z = self.cam.getZ(self.render)

                scale = [1, 1, 1]

                if self.surface_box is not None:
                    pos = [self.surface_box.getX(), self.surface_box.getY(), self.surface_box.getZ() +
                           (self.surface_box.getSz() + 1.8*scale[2]) / 2]
                    self.load_carrossel(pos, scale)
                    self.setupLights()
                    self.startCarousel()
                    print self.carousel.getPos(self.render)
                    print self.carousel.getPos(self.cam)
                else:
                    # pos = [x, y + 30, z]
                    # self.load_carrossel(pos, scale)
                    # self.setupLights()
                    # self.startCarousel()
                    # print self.carousel.getPos(self.render)
                    # print self.carousel.getPos(self.cam)
                    pos = [x, y + 30, z]
                    self.load_PS5(pos, scale)
                    print self.PS5.getPos(self.render)
                    print self.PS5.getPos(self.cam)

                self.cTrav.showCollisions(self.render)
                isObjectCreated = True

    # starts the calibration process to match SLAM to meters
    def startCalibration(self):
        x = self.cam.getX()
        y = self.cam.getY()
        z = self.cam.getZ()

        self.calibrator.setStart(x, y, z)

    # ends the calibration process
    def endCalibration(self):
        global calibrated

        x = self.cam.getX()
        y = self.cam.getY()
        z = self.cam.getZ()

        self.calibrator.setEnd(x, y, z)

        # sends the right dimensions to slam
        send_factor_to_slam(self.calibrator.converted)
        calibrated = True

    # open thread for initial position using object detection
    def thread_detect_object(self):
        object_thread = Thread(target=self.detect_object, args=())
        object_thread.start()

    # detects the real object and places the virtual object relative to the real one
    def detect_object(self):
        global canUpdateYOLO
        global yoloBB

        canUpdateYOLO = False
        marker_thread = Thread(target=object_detection, args=(yoloBB, ))
        marker_thread.start()
        marker_thread.join()
        yolo_output = yoloBB.replace('\t', '').replace('Object Detected: ', '').replace('(center_x:', '')\
            .replace('  center_y: ', '').replace('  width: ', '').replace('  height: ', '').replace(')', '')\
            .replace('\n', '').replace('%', '').replace(':', '')

        yolo_parameters = yolo_output.split(' ')
        label_number = self.label_yolo[yolo_parameters[0]]
        y = objectsize[label_number][0]*objectsize[label_number][2]*sizeimg_database[1]/(float(yolo_parameters[3])
                                                                                         * sizeimg_database[1])
        y *= METER * 5

        distance_center = (float(yolo_parameters[2]) - 0.5)*sizeimg_database[0]
        x = proportion_bb2cm[2] * distance_center / (proportion_bb2cm[0]*sizeimg_database[0])
        x *= METER * 5

        distance_center = (float(yolo_parameters[3]) - 0.5)*sizeimg_database[1]
        z = proportion_bb2cm[3] * distance_center / (proportion_bb2cm[1]*sizeimg_database[1])
        z *= METER * 5

        #temp = self.loader.loadModel("models/Dice_Obj.obj")
        #tex = self.loader.loadTexture('models/Dice_Base_Color.png')
        #tex.setWrapV(Texture.WM_repeat)
        #temp.setTexture(tex, 2)
        #temp.reparentTo(self.cam)
        #temp.setScale(1, 1, 1)
        #temp.setPos(x, y, z)

        #worldPosition = temp.getPos(self.render)
        #worldQuat = temp.getQuat(self.render)

        #temp.reparentTo(self.render)
        #temp.setPos(worldPosition)
        #temp.setQuat(worldQuat)

        temp = NodePath("NodePathWrenchAndCollision")
        temp.reparentTo(self.cam)
        temp.setPos(x, y, z)
        x1 = temp.getX(self.render)
        y1 = temp.getY(self.render)
        z1 = temp.getZ(self.render)
        worldQuat = temp.getQuat(self.render)

        #self.load_carrossel([x1, y1, z1], [1, 1, 1])
        #self.setupLights()
        #self.startCarousel()
        self.load_wrench([x1, y1, z1], [1, 1, 1])
        self.rotate_model(self.wrench)
        self.wrench.setQuat(worldQuat)

        self.cTrav.showCollisions(self.render)
        canUpdateYOLO = True

    # sets the plane detection and creation thread
    def set_plane(self):
        grid_thread = Thread(target=self.set_grid, args=())
        grid_thread.start()

    # sets the plane detection and creation thread with slam coordinates
    def set_plane_slam(self):
        grid_thread = Thread(target=self.get_slam_plane, args=())
        grid_thread.start()

    # get coordinates with variation in z small then 2 centimetres and take the average of measurements
    def get_slam_plane(self):
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
        self.set_grid(x, y, z)

    # creates the plane
    def set_grid(self, x=None, y=None, z=None):
        if x is None:
            x = self.cam.getX(self.render)
            y = self.cam.getY(self.render) + 50
            z = self.cam.getZ(self.render) - 20

        print "Centro do plano colocado em x: " + str(x) + " y: " + str(y) + " z: " + str(z)
        dx, dy, dz = 8, 8, 0.01

        print "Coordenadas Camera: " + str(self.cam.getPos()) + "\n"

        self.surface_box = self.loader.loadModel('models/cube.obj')
        self.surface_box.reparentTo(self.render)
        tex = self.loader.loadTexture('models/Gravel_diffuse.jpg')
        tex.setWrapU(Texture.WM_repeat)
        self.surface_box.setTexture(tex, 2)
        self.surface_box.setPos(x, y, z - dz)
        self.surface_box.setScale(dx, dy, dz)

        cNode = CollisionNode("SurfaceNode")
        cNode.addSolid(CollisionBox(LPoint3f(x, y, z - dz), dx, dy, dz))
        nodePath = NodePath("NodePath")
        self.collision_surface = nodePath.attachNewNode(cNode)
        self.collision_surface.reparentTo(self.render)

    # loads the wrench model
    def load_wrench(self, pos, scale):
        self.modelandcollision = NodePath("NodePathWrenchAndCollision")
        self.modelandcollision.setPos(pos[0], pos[1], pos[2])
        self.modelandcollision.reparentTo(self.pipeline)
        # Load screwdriver model
        self.wrench = self.loader.loadModel("models/wrench")
        # Apply scale and position transforms on the model.
        self.wrench.setScale(scale[0], scale[1], scale[2])
        #self.wrench.setP(90)
        self.wrench.reparentTo(self.modelandcollision)
        # this tells panda its a geom collision node
        cNode = CollisionNode("WrenchCollisionNode")

        cNode.addSolid(CollisionSphere(0, 0, 0, 0.45))

        wrenchCollision = self.wrench.attachNewNode(cNode)
        wrenchCollision.reparentTo(self.wrench)
        #wrenchCollision.show()
        self.cTrav.addCollider(wrenchCollision, self.pusher)
        self.pusher.addCollider(wrenchCollision, self.wrench, self.drive.node())

    #loads the screwdriver model
    def load_screwdriver(self, pos, scale):
        self.modelandcollision = NodePath("NodePathScrewdriverAndCollision")
        self.modelandcollision.setPos(pos[0], pos[1], pos[2])
        self.modelandcollision.reparentTo(self.pipeline)
        # Load screwdriver model
        self.screwdriver = self.loader.loadModel("models/screwdriver")
        # Apply scale and position transforms on the model.
        self.screwdriver.setScale(scale[0], scale[1], scale[2])
        self.screwdriver.reparentTo(self.modelandcollision)

        # set CollisionSpheres
        cNode = CollisionNode("ScrewdriverCollisionNode")

        for i in range(1, 30):
            if i < 13:
                cNode.addSolid(CollisionSphere(0, 0, self.screwdriver.getZ() + (i * 0.1), 0.25))
            else:
                cNode.addSolid(CollisionSphere(0, 0, self.screwdriver.getZ() + (i * 0.1), 0.10))

        screwdriverCollision = self.screwdriver.attachNewNode(cNode)
        self.cTrav.addCollider(screwdriverCollision, self.pusher)
        self.pusher.addCollider(screwdriverCollision, self.screwdriver, self.drive.node())

    #loads the PS5 model
    def load_PS5(self, pos, scale):
        self.modelandcollision = NodePath("NodePathPS5AndCollision")
        self.modelandcollision.setPos(pos[0], pos[1], pos[2])
        self.modelandcollision.reparentTo(self.pipeline)
        # Load the PS5 model
        self.PS5 = self.loader.loadModel("models/PS5")
        # Apply scale and position transforms on the model.
        self.PS5.setScale(scale[0], scale[1], scale[2])
        self.PS5.reparentTo(self.modelandcollision)
        # this tells panda its a geom collision node
        # set CollisionSpheres
        cNode = CollisionNode("PS5CollisionNode")

        for i in range(-9, 10):
            for j in range(1, 26):
                cNode.addSolid(CollisionSphere(i * 0.1, 0, self.PS5.getZ() + (j * 0.1), 0.25))

        PS5Collision = self.PS5.attachNewNode(cNode)
        self.cTrav.addCollider(PS5Collision, self.pusher)
        self.pusher.addCollider(PS5Collision, self.PS5, self.drive.node())

    # loads the carrousel model
    def load_carrossel(self, pos, scale):
        self.modelandcollision = NodePath("NodePathCarouselAndCollision")
        self.modelandcollision.setPos(pos[0], pos[1], pos[2])
        self.modelandcollision.reparentTo(self.render)
        # Load the carousel base
        self.carousel = self.loader.loadModel("models/carousel_base")
        self.carousel.setScale(scale[0], scale[1], scale[2])
        self.carousel.reparentTo(self.modelandcollision)

        self.lights1 = self.loader.loadModel("models/carousel_lights")
        self.lights1.reparentTo(self.carousel)

        self.lights2 = self.loader.loadModel("models/carousel_lights")
        self.lights2.setH(36)
        self.lights2.reparentTo(self.carousel)

        self.lightOffTex = self.loader.loadTexture("models/carousel_lights_off.jpg")
        self.lightOnTex = self.loader.loadTexture("models/carousel_lights_on.jpg")

        self.pandas = [self.carousel.attachNewNode("panda" + str(i))
                       for i in range(4)]
        self.models = [self.loader.loadModel("models/carousel_panda")
                       for i in range(4)]
        self.moves = [0] * 4

        for i in range(4):
            self.pandas[i].setPosHpr(0, 0, 1.3, i * 90, 0, 0)

            self.models[i].reparentTo(self.pandas[i])
            self.models[i].setY(.85)

        cNode = CollisionNode('carouselCollision')
        cNode.addSolid(CollisionSphere(0, 0, self.models[1].getZ(self.carousel), 1.8 * scale[0]))
        self.carouselC = self.carousel.attachNewNode(cNode)

        self.cTrav.addCollider(self.carouselC, self.pusher)
        self.pusher.addCollider(self.carouselC, self.carousel, self.drive.node())

    # enable the lights for the carrousel model
    def setupLights(self):
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor((.4, .4, .35, 1))
        directionalLight = DirectionalLight("directionalLight")
        directionalLight.setDirection(LVector3(0, 8, -2.5))
        directionalLight.setColor((0.9, 0.8, 0.9, 1))
        self.render.setLight(self.render.attachNewNode(directionalLight))
        self.render.setLight(self.render.attachNewNode(ambientLight))

    # enable the lights for the models
    def setupLightsModels(self):
        # pipeline for ambient light to see models materials
        self.pipeline = NodePath("NodePathIllumination")
        self.pipeline.reparentTo(self.render)
        alight = AmbientLight("alight")
        alight.setColor((1, 1, 1, 1))
        alnp = self.render.attachNewNode(alight)
        self.pipeline.setLight(alnp)

        # pipeline for ambient light to see models materials on Hands, because hands is attach to camera
        self.pipelineHands = NodePath("NodePathIlluminationHands")
        self.pipelineHands.reparentTo(self.cam)
        alnpHands = self.cam.attachNewNode(alight)
        self.pipelineHands.setLight(alnpHands)

    # start model
    def rotate_model(self, obj):
        self.spin = obj.hprInterval(20, LVector3(360, 0, 0))

        self.spin.loop()

    # starts the animation for the carrousel model
    def startCarousel(self):
        self.carouselSpin = self.carousel.hprInterval(20, LVector3(360, 0, 0))

        self.carouselSpin.loop()

        for i in range(4):
            self.moves[i] = LerpFunc(
                self.oscillatePanda,  # function to call
                duration=3,  # 3 second duration
                fromData=0,  # starting value (in radians)
                toData=2 * pi,  # ending value (2pi radians = 360 degrees)
                extraArgs=[self.models[i], pi * (i % 2)]
            )
            self.moves[i].loop()

        self.lightBlink = Sequence(
            Parallel(
                Func(self.lights1.setTexture, self.lightOnTex, 1),
                Func(self.lights2.setTexture, self.lightOffTex, 1)),
            Wait(1),
            Parallel(
                Func(self.lights1.setTexture, self.lightOffTex, 1),
                Func(self.lights2.setTexture, self.lightOnTex, 1)),
            Wait(1)
        )

        self.lightBlink.loop()

    # oscilates the pandas in the carrousel
    def oscillatePanda(self, rad, panda, offset):
        panda.setZ(sin(rad + offset) * .2)

    # keys handlers
    def defineKeys(self):
        self.accept('escape', sys.exit)
        self.accept('1', self.startCalibration)
        self.accept('2', self.endCalibration)
        self.accept('3', self.spawnObject)
        self.accept('4', self.initHands)
        self.accept('5', self.thread_detect_object)
        self.accept('6', self.set_plane_slam)

    def generateText(self):
        self.onekeyText = genLabelText("ESC: Sair", 1, self)
        self.onekeyText = genLabelText("[1] - Start SLAM Calibration", 2, self)
        self.onekeyText = genLabelText("[2] - End SLAM Calibration", 3, self)
        self.onekeyText = genLabelText("[3] - Spawn Object", 4, self)
        self.onekeyText = genLabelText("[4] - Activate GanHands", 5, self)
        self.onekeyText = genLabelText("[5] - Detect Object", 6, self)
        self.onekeyText = genLabelText("[6] - Set plane", 7, self)

