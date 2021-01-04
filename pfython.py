import pyaudio
import numpy as np
import matplotlib.pyplot as plt

CHUNK = 2048
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

window = np.blackman(CHUNK)
FREQUENCY_RANGE = (550, 3000)

class BasePfython:
    """ Handles most basic input. Records and analyses raw audio for higher-level usage """
    
    def __init__(
            self,
            chunk_size = CHUNK,
            format = FORMAT,
            channels = CHANNELS,
            rate = RATE,
    ):
        self.chunk_size = CHUNK
        self.rate = RATE
        self.pyaudio = pyaudio.PyAudio()
        self.stream = self.pyaudio.open(
                format=format,
                channels=channels,
                rate=rate,
                input=True,
                frames_per_buffer=chunk_size
            )
        self.history = []


    def read_input(self):
        """ Get input. Return frequencies and their intensities"""
        data = self.stream.read(self.chunk_size)
        signal = np.frombuffer(data, 'Int16')
        signal = signal * window    # Aus dem Internetz. Seems to be gud
        intensities = np.abs(np.fft.rfft(signal))
        freqs = np.fft.rfftfreq(self.chunk_size, 1./self.rate)
        # freqs_in_hertz = abs(freqs * self.rate)
        return freqs, intensities, signal


    def analyse_input(self, freqs, intensities):
        """ Return if there is whistling in the data + the dominant frequency """
        # Find the peak in the coefficients
        idx = np.argmax(np.abs(intensities))
        max_freq = freqs[idx]
        # freq_in_hertz = abs(freq * RATE)
        max_intensity = np.log10(abs(intensities[idx]))
        # Test if intensity is strong enough and in frequency range
        if max_intensity < 4.5 or max_freq < FREQUENCY_RANGE[0]:
            # no whistle
            return False, 0

        # Cut out strongest peak (+- 5 Hz). Whistle peak must be at least 0.5 dB louder than anything else
        idx_without_peak = [i for i in range(len(freqs)) if abs(freqs[i] - max_freq) > 5]
        maxima_idx = sorted(idx_without_peak, key=lambda i: np.abs(intensities)[i], reverse=True)
        max_intensities = np.log10(np.abs(intensities))

        if max_intensity - max_intensities[maxima_idx[5]] >= 0.5:
            return True, max_freq
        else:
            return False, 0


    def plot_input(self, freqs, intensities):
        plt.plot(freqs, intensities)
        # plt.xscale('log')
        plt.show()


    def show_live(self):
        plt.ion()
        fig = plt.figure()
        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212)
        log_scale = True

        while True:
            freqs, intensities, signal = source.read_input()
            whistle, max_freq = self.analyse_input(freqs, intensities)
            ax1.cla()
            # ax1.set_ylim(1, 7)
            # ax1.set_ylim(0, 5e6)
            ax1.set_ylim(1, 3e6)
            ax1.set_xlim(550, 3000)
            ax1.grid()
            if whistle:
                ax1.axvline(max_freq, linestyle='--')
            ax1.plot(freqs, intensities)
            if log_scale:
                ax1.set_yscale('log')
            # ax1.set_xscale('log', basex=2)

            ax2.cla()
            ax2.plot(signal)
            ax2.set_ylim(-5000, 5000)
            plt.pause(0.0001)


    def show_history(self):
        plt.ion()
        fig = plt.figure()
        ax1 = fig.add_subplot(111)

        while True:
            freqs, intensities, signal = source.read_input()
            whistle, max_freq = self.analyse_input(freqs, intensities)

            if len(self.history) >= 30:
                self.history.pop(0)
            self.history.append((whistle, max_freq))

            ax1.cla()
            ax1.set_ylim(550, 3000)
            for i in range(1, len(self.history)):
                last_whistle, current_whistle = self.history[i-1][0], self.history[i][0]
                if last_whistle and current_whistle:
                    linestyle = '--'
                else:
                    linestyle = ''

                ax1.plot([i-1, i], [self.history[i-1][1], self.history[i][1]], linestyle=linestyle, color='b', marker='.')
            # ax1.plot([datapoint[1] for datapoint in self.history if datapoint[0]])
            plt.pause(0.0001)


if __name__ == '__main__':
    source = BasePfython()
    # freqs, intensities = source.read_input()
    # source.plot_input(freqs, intensities)
    source.show_history()