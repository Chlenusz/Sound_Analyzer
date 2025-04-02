from typing import Literal
import pygame
import numpy as np


class Visualiser:

    def __init__(self):
        pygame.display.set_caption("Visualiser")
        self.running = False
        self.paused = False
        self.width = 1200
        self.height = 600
        self.window_size = (self.width, self.height)
        self.screen: pygame.Surface = None
        self.baseLevel = self.height-20
        self.x_axis = []
        self.y_axis =[]
        self.white = (255,255,255)
        self.black = (0,0,0)

    def reset(self):
        self.running = True
        self.paused = False
        self.x_axis = []
        self.y_axis = []
        pygame.quit()
        pygame.init()
        pygame.display.set_caption("Visualiser")
        self.screen = pygame.display.set_mode(self.window_size)

    @staticmethod
    def close():
        pygame.display.quit()

    def isPaused(self):
        return self.paused

    def isRunning(self):
        return self.running

    def update(self, interpolation_mode: bool = True):
        if not self.paused:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    self.paused = True
                    pygame.display.quit()
                    return None
            # Drawing
            self.screen.fill(self.black)

            if not interpolation_mode:
                points: list[(float,float)] = self.calculatePoints()
                for point in points:
                    pygame.draw.circle(self.screen, self.white, point, 1)
            else:
                self.genXaxis()
                self.interpolate(level=2, mode="valid")
                self.flipYaxis()
                points = list(zip(self.x_axis, self.y_axis))
                pygame.draw.lines(self.screen, self.white, False, points, 3)

            pygame.display.flip()

    def interpolate(self, mode: Literal["valid", "same", "full"] = "same", level: int = 10):
        window_size = level
        kernel = np.ones(window_size) / window_size
        self.y_axis = np.convolve(self.y_axis, kernel, mode=mode)

    def genXaxis(self):
        init_len = len(self.x_axis)
        self.x_axis = np.linspace(20, self.width-20, init_len).tolist()

    def genYaxis(self, scale: float = 1.0):
        init_len = len(self.y_axis)
        for i in range(0, init_len):
            self.y_axis[i] = self.baseLevel-self.y_axis[i]*scale

    def calculatePoints(self):
        self.genXaxis()
        self.genYaxis()
        return list(zip(self.x_axis,self.y_axis))

    def flipYaxis(self):
        self.y_axis *= -1
        self.y_axis += 500

    def transformData(self, raw_data):
        self.y_axis, self.x_axis = raw_data







