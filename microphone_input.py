import pyaudio
import numpy as np


class AudioDevice:

    def __init__(self):
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.chunk = 2048
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format= self.format, channels=self.channels, rate=self.rate,
                                  input=True, frames_per_buffer=self.chunk)

    def getData(self):
        data = self.stream.read(self.chunk, exception_on_overflow=False)
        audio = np.frombuffer(data, dtype=np.int16)
        return audio

    def debug(self):
        data = self.stream.read(self.chunk, exception_on_overflow=False)
        audio_np = np.frombuffer(data, dtype=np.int16)  # Convert to NumPy array
        print("Audio Data:", audio_np)  # Print first 10 samples for debugging




if __name__ == "__main__":
    a = AudioDevice()
    a.debug()
