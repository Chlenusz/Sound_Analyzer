import tkinter as tk
from threading import Thread
from threading import Event
import time
from fun import Visualiser
from analyzer import App
from music_player import Player
from tkinter import messagebox
from microphone_input import AudioDevice


class Window:

    def __init__(self) -> None:
        self.debugMode: bool = False
        self.interpolation_mode = True
        self.raw_data_mode = True
        self.dBMode = False
        self.noiseReduction = False
        self.microphone_mode = False
        self.pipe_thread: Thread = Thread(target=self.visualizeData)
        self.end_event = Event()
        self.analyzer = App()
        self.visualizer = Visualiser()
        self.player = Player()
        self.recorder = AudioDevice()
        self.window = tk.Tk()
        self.varInterpolation = tk.BooleanVar()
        self.varRawData = tk.BooleanVar()
        self.varMagnitude = tk.BooleanVar()
        self.varMicrophone = tk.BooleanVar()
        self.varNoiseReduction = tk.BooleanVar()
        self.window.title("Audio Analyzer")

        self.initButton = tk.Button(self.window, text="Initialize")
        self.startButton = tk.Button(self.window, text="Start Visualizing")
        self.debugAnalyzerButton = tk.Button(self.window, text="Debug Analyzer")
        self.debugVisualiserButton = tk.Button(self.window, text="Debug Visualiser")
        self.volumeBox = tk.Spinbox(self.window)
        self.interpolationButton = tk.Checkbutton(self.window, text="Interpolation")
        self.rawDataButton = tk.Checkbutton(self.window, text="Raw Data")
        self.volumeLabel = tk.Label(self.window, text="Set volume:")
        self.pauseButton = tk.Button(self.window, text="Pause")
        self.debugWindow = tk.Button(self.window, text="Debug Window")
        self.errorLabel = tk.Label(self.window, text="")
        self.magnitudeButton = tk.Checkbutton(self.window, text="dB")
        self.microphoneButton = tk.Checkbutton(self.window, text="Microphone enabled")
        self.noiseButton = tk.Checkbutton(self.window, text="Noise Reduction")

        self.setGrid()
        self.setCommands()

        self.window.geometry("350x200")
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()

    def setGrid(self) -> None:
        self.initButton.grid(row=0, column=1)
        self.startButton.grid(row=1, column=1)
        self.microphoneButton.grid(row=2, column=1, sticky="W")
        self.errorLabel.grid(row=5, column=1)

        if self.debugMode:
            self.debugAnalyzerButton.grid(row=2, column=1)
            self.debugVisualiserButton.grid(row=3, column=1)
            self.debugWindow.grid(row=4, column=1)

        self.volumeBox.grid(row=1,column=0)
        self.volumeLabel.grid(row=0,column=0)
        self.pauseButton.grid(row=2,column=0)

        self.interpolationButton.grid(row=0,column=2, sticky="W")
        self.magnitudeButton.grid(row=1, column=2, sticky="W")
        self.noiseButton.grid(row=2, column=2, sticky="W")

    def setCommands(self) -> None:
        self.initButton.configure(command=self.initAnalysis)
        self.startButton.configure(command=self.threadedPipe,state="disabled")
        self.debugAnalyzerButton.configure(command=self.analyzer.debug)
        self.volumeBox.configure(command=lambda: self.player.changeVolume(self.volumeBox.get()), from_=0, to=100, width=10)
        self.interpolationButton.configure(variable=self.varInterpolation, command=lambda: self.setInterpolationMode(self.varInterpolation.get()))
        self.interpolationButton.select()
        self.rawDataButton.configure(variable=self.varRawData, command=lambda: self.setRawDataMode(self.varRawData.get()))
        self.rawDataButton.select()
        self.volumeBox.insert(0, "5")
        self.pauseButton.configure(command=self.pause)
        self.debugWindow.configure(command=self.debugThread)
        self.magnitudeButton.configure(variable=self.varMagnitude, command=lambda: self.setMagnitudeMode(self.varMagnitude.get()))
        self.microphoneButton.configure(variable=self.varMicrophone, command=lambda: self.setMicrophoneMode(self.varMicrophone.get()))
        self.noiseButton.configure(variable=self.varNoiseReduction, command=lambda: self.setNoiseReduction(self.varNoiseReduction.get()))

    def debug(self):
        self.resetComps()
        self.disableStart()
        self.disableInit()

        while not self.end_event.is_set():

            if not self.visualizer.isPaused():
                start_time = time.time()
                analog_data = self.recorder.getData()
                analog_specs = self.recorder.rate
                data = (analog_data, analog_specs)


                data = self.analyzer.getData(microphone_mode=True, data=data, dBMode=self.dBMode)

                self.visualizer.transformData(data)
                self.visualizer.update(interpolation_mode=self.interpolation_mode)
                end_time = time.time()
                print(f"Processing time: {-start_time + end_time}")
            else:
                break
        self.visualizer.running = False
        self.end_event.set()
        self.resetEvent()
        self.enableStart()
        self.enableInit()

    def debugThread(self):
        Thread(target=self.debug).start()

    def setInterpolationMode(self, var: bool):
        self.interpolation_mode = var

    def setRawDataMode(self, var: bool):
        self.raw_data_mode = var

    def setMagnitudeMode(self, var: bool):
        self.dBMode = var

    def setNoiseReduction(self, var: bool):
        self.noiseReduction = var

    def setMicrophoneMode(self, var: bool):
        self.microphone_mode = var
        if self.microphone_mode:
            self.enableStart()
        else:
            self.disableStart()

    def initAnalysis(self):
        initialized = self.analyzer.prepareData()
        if initialized:
            self.enableStart()
        else:
            self.disableStart()

    def disableInit(self):
        self.initButton.configure(state="disabled")

    def enableInit(self):
        self.initButton.configure(state="active")

    def disableStart(self):
        self.startButton.configure(state="disabled")

    def enableStart(self):
        self.startButton.configure(state="active")

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.pause()
            self.visualizer.running = False
            self.player.stopMusic()
            self.player.exit()
            self.visualizer.close()
            self.analyzer.cleanWorkFolder()
            self.end_event.set()
            self.window.quit()

    def pause(self):
        if self.player.isPaused():
            self.player.paused = False
            self.player.unpauseMusic()
            self.visualizer.paused = False
            self.pauseButton.configure(text="Unpause")
        else:
            self.player.paused = True
            self.player.pauseMusic()
            self.visualizer.paused = True
            self.pauseButton.configure(text="Pause")

    @staticmethod
    def reset(entry: any) -> None:
        last_num = len(entry.get()) + 1
        entry.delete(0, last_num)

    def resetComps(self):
        self.visualizer.reset()
        self.player.reset()
        self.analyzer.reset()

    def visualizeData(self):
        self.resetComps()
        self.disableStart()
        self.disableInit()

        if not self.microphone_mode:
            self.player.setNewMusic(self.analyzer.getFileDest())
            self.player.playMusic()

        while not self.end_event.is_set():
            if self.microphone_mode:
                if not self.visualizer.isPaused():
                    data = self.processMicrophone()
                    self.visualizer.transformData(data)
                    self.visualizer.update(interpolation_mode=self.interpolation_mode)
                else:
                    break
            else:
                if not self.visualizer.isRunning():
                    self.player.stopMusic()
                    break
                if not self.player.isPaused() and not self.visualizer.isPaused():


                    music_time = self.player.getCurrentTime() / 1000
                    anal_time = self.analyzer.getCurrentTimeFrame()
                    dtime = music_time - anal_time

                    if dtime > 0:
                        data = self.analyzer.getData(latency_skip=dtime, microphone_mode=False, dBMode=self.dBMode)
                    elif dtime < -0.05:
                        time.sleep(abs(dtime))
                        data = self.analyzer.getData(microphone_mode=False, dBMode=self.dBMode)
                    else:
                        data = self.analyzer.getData(microphone_mode=False, dBMode=self.dBMode)

                    if data is None:
                        print("End of data")
                        break
                    self.visualizer.transformData(data)
                    self.visualizer.update(interpolation_mode=self.interpolation_mode)
        self.visualizer.running = False
        if not self.microphone_mode:
            if not self.end_event.is_set():
                self.player.stopMusic()
        self.end_event.set()
        self.resetEvent()
        self.enableStart()
        self.enableInit()

    def threadedPipe(self):
        self.pipe_thread: Thread = Thread(target=self.visualizeData)
        self.pipe_thread.start()

    def processMicrophone(self):
        analog_data = self.recorder.getData()
        analog_specs = self.recorder.rate
        data = (analog_data, analog_specs)

        newData = self.analyzer.getData(microphone_mode=True, data=data, dBMode=self.dBMode,  noiseReduction=self.noiseReduction)
        return newData

    def resetEvent(self):
        self.end_event = Event()


if __name__ == '__main__':
    Window()
