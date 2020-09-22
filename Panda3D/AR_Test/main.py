from panda3d.core import loadPrcFileData, CardMaker, MovieTexture, Filename
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
        self.tex = MovieTexture(option)
        #self.tex .setKeepRamImage(True)
        #print("WebCamVideo based texture infos: -> {0}".format(self.tex ))


        # create a card which shows the image captured by the webcam.

        cm = CardMaker("background-card")

        cm.setFrame(-1, 1, 1, -1)

        card = self.render2d.attachNewNode(cm.generate())

        card.setTexture(self.tex)

        # set the rendering order manually to render the card-with the webcam-image behind the scene.

        self.cam.node().getDisplayRegion(0).setSort(20)

        # initialize artoolkit, self.cam is our camera ,
        # the camera_para.dat is the configuration file for your camera. this one comes with the artoolkit installation.
        # last paremeter is the size of the pattern in panda-units.

        self.ar = ARToolKit.make(self.cam, Filename(self.mainDir, "ar/camera_para.dat"), 1)
        #print(self.ar)

        # load a model to visualize the tracking
        axis = self.loader.loadModel("models/ball")
        axis.reparentTo(self.render)
        axis.setScale(0.25, 0.25, 0.25)


        # attach the model to a pattern so it updates the model's position relative to the camera each time we call analyze()

        self.ar.attachPattern(Filename(self.mainDir, "ar/patt.sample1"), axis)

        # updating the models positions each frame.

        sleep(1)  # some webcams are quite slow to start up so we add some safety

        self.taskMgr.add(self.updatePatterns, "update-patterns")

    def updatePatterns(self, task):
        self.ar.analyze(self.tex, True)
        return Task.cont

demo = ARtest()
demo.run()