import pygame.mixer
import pygame.mixer as mixer


class Player:

    def __init__(self):
        pygame.mixer.init()
        self.default_volume = 50
        self.track_dest = None
        self.paused = False

    @staticmethod
    def reset():
        pygame.mixer.quit()
        pygame.mixer.init()

    @staticmethod
    def initMixer():
        mixer.init()

    def isPaused(self):
        return self.paused

    def playMusic(self):
        mixer.music.load(self.track_dest)
        self.changeVolume(self.default_volume)
        mixer.music.play()

    @staticmethod
    def stopMusic():
        mixer.music.stop()
        mixer.music.unload()

    def setNewMusic(self, dest):
        self.track_dest = dest

    @staticmethod
    def changeVolume(vol):
        volume = (float(vol)/100.)
        mixer.music.set_volume(volume)

    def pauseMusic(self):
        self.paused = True
        mixer.music.pause()

    def unpauseMusic(self):
        self.paused = False
        mixer.music.unpause()

    @staticmethod
    def exit():
        mixer.quit()

    @staticmethod
    def getCurrentTime():
        return mixer.music.get_pos()

