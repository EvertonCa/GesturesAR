from panda3d.core import loadPrcFileData, CardMaker, MovieTexture, Filename, Vec2, Point2
from direct.showbase.ShowBase import ShowBase
from panda3d.vision import WebcamVideo, ARToolKit
from direct.task import Task
from time import sleep
loadPrcFileData("", "auto-flip 1")  # usualy the drawn texture lags a bit behind the calculted positions. this is a try to reduce the lag.

class ARtest(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        # ------use OpenCVTexture under linux---------- use WebcamVideo under windows------------
        option = WebcamVideo.getOption(0)  # 0 here is default webcam, 1 would be second cam etc.
        #self.cursor = option.open()
        self.tex = MovieTexture(option)
        self.tex.setTexturesPower2(0)
        #self.tex.setKeepRamImage(True)
        #self.cursor.setupTexture(self.tex)
        print("WebCamVideo based texture infos: -> {0}".format(self.tex))
        videoTextureScale = Vec2(option.getSizeX() / float(self.tex.getXSize()),
                                 option.getSizeY() / float(self.tex.getYSize()))



        # create a card which shows the image captured by the webcam.
        cm = CardMaker("background-card")
        cm.setUvRange(Point2(videoTextureScale[0], 0), Point2(0, videoTextureScale[1]))
        cm.setFrame(-videoTextureScale[1], videoTextureScale[1], -videoTextureScale[0], videoTextureScale[0])
        card = self.render2d.attachNewNode(cm.generate())
        card.setTexture(self.tex)

        # set the rendering order manually to render the card-with the webcam-image behind the scene.
        self.cam.node().getDisplayRegion(0).setSort(20)

        # initialize artoolkit, self.cam is our camera ,
        # the camera_para.dat is the configuration file for your camera. this one comes with the artoolkit installation.
        # last parameter is the size of the pattern in panda-units.
        self.ar = ARToolKit.make(self.cam, Filename(self.mainDir, "ar/camera_para.dat"), 0)

        # load a model to visualize the tracking
        self.addObject()

        # updating the models positions each frame.
        sleep(1)  # some webcams are quite slow to start up so we add some safety
        self.taskMgr.add(self.updatePatterns, "update-patterns")

    def addObject(self):
        axis = self.loader.loadModel("teapot.egg")
        axis.reparentTo(self.render)
        #axis.setScale(0.25, 0.25, 0.25)

        # attach the model to a pattern so it updates the model's position relative to the camera each time we call analyze()
        self.ar.attachPattern(Filename(self.mainDir, "ar/patt.sample1"), axis)  # -> Falta validar esse arquivo de pattern

    def updatePatterns(self, task):
        self.ar.analyze(self.tex, True)
        return Task.cont

demo = ARtest()
demo.run()