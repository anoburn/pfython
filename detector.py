import numpy as np
import pickle
import logging
from pfython import BasePfython

logging.basicConfig(format='Detector')

# Number of datapoints for saved/analysed intervals
OBSERVED_LENGTH = 40

# [1318.51, 987.77, 783.99, 1318.51]
# [698.46, 880.00, 1046.50, 1396.91, 1760.00, 1567.98, 1396.91, 1174.66, 987.77, 1046.50]
SIGNALS_RAW = {
    0: [1318.51, 987.77, 783.99, 1318.51],
    1: [698.46, 880.00, 1046.50, 1396.91, 1760.00, 1567.98, 1396.91, 1174.66, 987.77, 1046.50],
    2: [1318.51, 1174.66, 1046.50, 987.77, 987.77, 1046.50, 987.77, 783.99]
}

SIGNALS = {key: [np.log2(val) - np.log2(vals[0]) for val in vals] for key, vals in SIGNALS_RAW.items()}

class Detector:
    def __init__(self):
        self.source = BasePfython()
        self.reset()

    def reset(self):
        """ Clear collected data """
        self.whistles = [False for _ in range(OBSERVED_LENGTH)]
        self.freqs = [0 for _ in range(OBSERVED_LENGTH)]
        self.sample_data = {}

    def update(self):
        """ Main update method. Sample audio and detect signals """
        self.update_data()
        signal_key, signal_freqs = self.detect_signal()
        if signal_key is not None:
            self.reset()    # clear collected data to avoid repeated detection
            print(f'Found signal {signal_key}')

    def update_data(self):
        """ Record chunk of audio, analyze, add result to memory """
        freqs, intensities, signal = self.source.read_input()
        whistle, max_freq = self.source.analyse_input(freqs, intensities)
        # if whistle:
        #     print(f'whistle = {whistle}   freq = {max_freq}')
        self.whistles.pop(0)
        self.freqs.pop(0)
        self.whistles.append(whistle)
        self.freqs.append(max_freq)

    def detect_signal(self):

        sample_freq = np.array(self.freqs)
        sample_whistle = self.whistles
        # Avoid division by zero warning
        sample_freq = np.where(sample_freq == 0, np.NaN, sample_freq)
        # print(f'{sample_freq * sample_whistle}')

        # check each known signal
        for signal_key, signal_val in SIGNALS.items():
            whistle_signal_raw = [val for i, (val, whistle) in enumerate(zip(np.log2(sample_freq), sample_whistle)) if whistle]
            if len(whistle_signal_raw) > 2:
                # normalize recorded whistling to first value
                whistle_signal = [v - whistle_signal_raw[0] for v in whistle_signal_raw]
                i_signal, i_record = 0, 0
                while i_record < len(whistle_signal):
                    # if i_signal > 0 and signal_key == 1:
                    #     print(f'Signal {signal_key} - Looking for note {i_signal}. Distance: {abs(whistle_signal[i_record] - signal_val[i_signal])}')
                    if i_signal > 0:
                        overshoot = 0
                        # signal is rising
                        if signal_val[i_signal - 1] < signal_val[i_signal]:
                            overshoot = whistle_signal[i_record] - signal_val[i_signal]
                        # signal is falling. just to be sure, maybe there is a signal with twice the same note ¯\_(ツ)_/¯
                        elif signal_val[i_signal - 1] > signal_val[i_signal]:
                            overshoot = signal_val[i_signal] - whistle_signal[i_record]
                        if overshoot > 0.40:
                            # print(f'Overshoot in signal {signal_key}!')
                            break
                    if abs(whistle_signal[i_record] - signal_val[i_signal]) < 0.08:
                        # if i_signal > 0:
                        #     print(f'Found note {i_signal}')
                        i_signal += 1
                        i_record += 1
                        # Signal completely found
                        if i_signal == len(signal_val):
                            return signal_key, whistle_signal
                    else:
                        i_record += 1

        return None, ''