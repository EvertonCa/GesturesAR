from panda3d.core import loadPrcFileData
from panda3d.vision import WebcamVideo
from panda3d.core import CardMaker, Point2, MovieTexture
from direct.showbase.ShowBase import ShowBase
import sys

loadPrcFileData("", "textures-power-2 none")
loadPrcFileData('', 'client-sleep 0.001')


class WebCamTest(ShowBase):

    def __init__(self):
        ShowBase.__init__(self)
        # using WebcamVideo
        self.printWebOptions()

        option = WebcamVideo.getOption(0)
        videoTexture = MovieTexture(option)
        videoTexture.setKeepRamImage(True)
        print("WebCamVideo based texture infos: -> {0}".format(videoTexture))

        cm = CardMaker("card")
        cm.setUvRange(Point2(0, 0), Point2(1, 1))
        cm.setFrame(-1, 1, -1, 1)
        card = self.render.attachNewNode(cm.generate())
        card.setTexture(videoTexture)
        card.setPos(0, 5, 0)
        card.reparentTo(self.render)

        self.accept('escape', lambda: sys.exit())

    def printWebOptions(self):
        for i in WebcamVideo.getOptions():
            print(i)



app = WebCamTest()
app.run()