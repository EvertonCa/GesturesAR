from click._compat import raw_input
from panda3d.core import loadPrcFileData
from panda3d.vision import WebcamVideo
from panda3d.core import CardMaker, Point2, MovieTexture
from direct.showbase.ShowBase import ShowBase
import sys

loadPrcFileData("", "textures-power-2 none") #the webcam feed can not be made into a power of two texture
loadPrcFileData("", "show-frame-rate-meter 1") #show fps
loadPrcFileData("", "sync-video 0") #turn off v-sync
loadPrcFileData("", "auto-flip 1") #usualy the drawn texture lags a bit behind the calculted positions. this is a try to reduce the lag.


class WebCamTest(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        #using WebcamVideo
        for x, option in enumerate(WebcamVideo.getOptions()):
            print(option, x)
        print("Choose webcam and resolution by index:")

        # Starting Webcam and placing the feed on the background card
        option = WebcamVideo.getOption(int(raw_input()))
        #option = WebcamVideo.getOption(0)

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


app = WebCamTest()
app.run()