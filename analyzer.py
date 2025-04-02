from exceptions_pack import *
import time
import sounddevice as sd
import bisect
from tkinter import filedialog
import os
from scipy.io import wavfile
import subprocess
import numpy as np
import noisereduce as nr


class App:
    def __init__(self):
        self.file = None
        self.destination = None
        self.current_codec = None
        self.data = None
        self.total_samples = None
        self.total_time = None
        self.sample_range = None
        self.noise_profile = None
        self.have_noise_profile = False
        self.sample_end = 0
        self.file_dest = "work_space/fixed_file.wav"
        self.samplerate: int = 0
        self.time_period: float = 0.03

    def debug(self):
        pass

    def getData(self, microphone_mode: bool = False, dBMode: bool = True, data=None, noiseReduction: bool = False, latency_skip = 0, hanningFilter: bool = True):
        return self.processAudioSignal(externalDataMode=microphone_mode,
                                       data=data,
                                       dBMode=dBMode,
                                       start_sample=self.sample_end,
                                       latency_skip=latency_skip,
                                       noiseReduction=noiseReduction,
                                       hanningFilter=hanningFilter)

    def getFileDest(self):
        return self.file_dest

    def getCodec(self):
        return self.current_codec

    def reset(self):
        self.sample_end = 0

    def prepareData(self) -> bool:
        try:
            print("Cleaning")
            if os.path.exists(self.file_dest):
                self.cleanWorkFolder()
            self.destination = filedialog.askopenfilename(title="Wybierz plik audio")
            if self.destination == "\"\"" or self.destination == "":
                raise DestinationError
            print("Checking codec")
            file_type, err = self.getAudioCodec()
            if err == -1:
                raise CheckingError
            if file_type == "":
                raise CheckingError
            if file_type != "wav":
                print("Generating temporary file")
                err = self.genWAVFile()
                if err == -1:
                    raise GenerationError
            self.current_codec = file_type
            if not os.path.exists(self.file_dest):
                raise GenerationError
            print("Reading data")
            self.readData()
        except DestinationError:
            print("Could not find set destination")
            return False
        except CheckingError:
            print("Codec type is invalid")
            return False
        except GenerationError:
            print("Could not generate ")
            return False
        else:
            print("Ready to work")
            return True

    def cleanWorkFolder(self) -> None:
        try:
            os.remove(self.file_dest)
        except FileNotFoundError:
            print(f"File {self.file_dest} not found.")
        except PermissionError:
            print(f"Permission denied to delete {self.file_dest}.")
        except Exception as e:
            print(f"Error occurred: {e}")

    def getDataSpecs(self):
        return self.samplerate, self.time_period

    def readData(self):
        self.samplerate, self.data = wavfile.read(self.file_dest)
        self.total_time = len(self.data) / self.samplerate
        self.sample_range = np.arange(0, self.total_time, self.time_period)
        self.total_samples = len(self.sample_range)
        return self.samplerate, self.data

    def getAudioCodec(self) -> tuple[str, int]:
        command = [
            "ffprobe",
            "-i", self.destination,
            "-v", "quiet",
            "-select_streams", "a:0",
            "-show_entries", "stream=codec_name",
            "-of", "default=noprint_wrappers=1:nokey=1"

        ]

        result = subprocess.run(command, capture_output=True, text=True)
        error = 0
        return result.stdout.strip(), error  # Remove any leading/trailing whitespace

    def genWAVFile(self) -> int:
        command = [
                "ffmpeg",
                "-v",
                "quiet",
                "-i",
                self.destination,
                "-acodec", "pcm_s16le",
                "-ar", "44100",
                self.file_dest
            ]
        try:
            subprocess.run(command)
        except subprocess.CalledProcessError as e:
            print(e.output)
        err = 0

        return err

    def getCurrentTimeFrame(self):
        return len(self.data[0:self.sample_end])/self.samplerate

    def noiseGate(self, data, sample_rate=44100):
        return nr.reduce_noise(y=data, sr=sample_rate, y_noise=self.noise_profile)

    def getNoiseProfile(self,duration, sample_rate):
        noise_profile = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
        sd.wait()
        self.noise_profile = noise_profile
        return noise_profile.flatten()

    @staticmethod
    def hanningFilter(samples_number, signal) -> np.ndarray:
        return signal * np.hanning(samples_number)

    def isSampleEnd(self) -> bool:
        return self.sample_end > len(self.data)

    def getFrames(self, latency_skip: float = 0., start_sample: int = 0):
        latency_frames = int(latency_skip * self.samplerate)
        normal_frames = int(self.time_period * self.samplerate)

        self.sample_end = start_sample + normal_frames + latency_frames

        return latency_frames

    @staticmethod
    def getMagnitude_dB(magnitude):
        if max(magnitude) != 0:
            magnitude = 20 * np.log10(magnitude / max(magnitude))
            magnitude -= min(magnitude)
        return magnitude

    @staticmethod
    def apply_correction_curve(magnitude, freqs, dBMode=True):
        # Define correction points (these are known points of correction)
        correction_points_freqs = np.array([10, 20, 40, 80, 100, 315, 500, 1000, 5000, 10000, 12500, 20000])
        correction_values = np.array([-68, -47, -33, -20, -18, -5, -2, 0, 0, -3, -5, -9])  # dB adjustments at those frequencies
        # Interpolate the correction values to match the FFT frequency bins
        if dBMode:
            correction_curve = np.interp(freqs, correction_points_freqs, correction_values)
        else:
            correction_values = correction_values/3*2
            correction_curve = np.interp(freqs, correction_points_freqs, correction_values)

        # Apply the correction to the magnitude spectrum
        corrected_magnitude = magnitude + correction_curve
        return corrected_magnitude

    def getFFT(self, signal, sample_num, onlyPositive=True, N=8192):
        if len(signal) < N:
            fft_result = np.fft.fft(signal, n=N)
            freqs= np.fft.fftfreq(n=N, d=(1/self.samplerate))
        else:
            fft_result = np.fft.fft(signal)
            freqs = np.fft.fftfreq(n=sample_num, d=(1/self.samplerate))

        # Wybór tylko dodatnich częstotliwości
        if onlyPositive:

            # magnitude = np.abs(fft_result)[range(int(N/2))]
            # freqs = abs(freqs)[range(int(N/2))]

            magnitude = np.abs(fft_result[:sample_num // 2])
            freqs = np.abs(freqs[:sample_num // 2])
        else:
            magnitude = np.abs(fft_result)
        index = bisect.bisect_left(freqs, 6000)
        if index is not None:
            freqs = freqs[:index]
            magnitude = magnitude[:index]

        return magnitude, freqs

    def processAudioSignal(self, data, externalDataMode: bool = False, dBMode=True, noiseReduction=False, hanningFilter=True, start_sample: int = 0, latency_skip: float = 0):
        if not externalDataMode:
            # Get latency and end frames
            latency_frames = self.getFrames(latency_skip, start_sample)

            if self.isSampleEnd():
                return None

            signal = self.data[start_sample + latency_frames:self.sample_end]

            # Obsługa sygnału stereo - konwersja do mono
            if len(signal.shape) == 2:
                signal = signal.sum(axis=1) / 2

            N = signal.shape[0]  # Liczba próbek
            if hanningFilter:
                signal = self.hanningFilter(N, signal)

            magnitude, freqs = self.getFFT(signal=signal, sample_num=N, onlyPositive=True)
        else:
            data, samplerate = data
            self.samplerate = samplerate
            signal = np.array(data, dtype=np.float32, copy=True)

            if noiseReduction:
                if not self.have_noise_profile:
                    self.noise_profile = self.getNoiseProfile(1, self.samplerate)
                    self.have_noise_profile = True
                    # time.sleep()
                signal = self.noiseGate(signal, samplerate)

            if len(signal.shape) == 2:
                signal = signal.sum(axis=1) / 2

            N = signal.shape[0]  # Liczba próbek
            if hanningFilter:
                signal = self.hanningFilter(N, signal)

            magnitude, freqs = self.getFFT(signal=signal, sample_num=N, onlyPositive=True)

        if dBMode:
            if max(magnitude) != 0:
                magnitude = self.getMagnitude_dB(magnitude)
                magnitude = self.apply_correction_curve(magnitude=magnitude, freqs=freqs,dBMode=True)
        else:
            if max(magnitude) != 0:
                magnitude = (magnitude/max(magnitude))*500
                magnitude = self.apply_correction_curve(magnitude=magnitude, freqs=freqs,dBMode=False)
        return magnitude, freqs

