import numpy as np
import pickle
import logging

logging.basicConfig(format='Detector')

# Number of datapoints for saved/analysed intervals
OBSERVED_LENGTH = 30

# SIGNALS = {
#     'HL': 0,
#     'LH': 1
# }

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
        self.reset()

    def reset(self):
        self.whistles = [False for _ in range(OBSERVED_LENGTH)]
        self.freqs = [42 for _ in range(OBSERVED_LENGTH)]
        self.sample_data = {}

    def compare_blocks(self, freqs_a, whistle_a, freqs_b, whistle_b):
        """ Compute 'distance' of two blocks with same length """
        assert len(freqs_a) == len(whistle_a)
        assert len(freqs_a) == len(freqs_b)
        assert len(freqs_a) == len(whistle_b)
        if isinstance(freqs_a, list):
            freqs_a = np.array(freqs_a)
        if isinstance(freqs_b, list):
            freqs_b = np.array(freqs_b)

        # freqs_a = np.array([datapoint[1] for datapoint in a])
        # whistle_a = [datapoint[0] for datapoint in a]
        freqs_a = freqs_a - np.mean(freqs_a[whistle_a])
        # freqs_a = freqs_a - np.mean(np.where(whistle_a, freqs_a))
        # freqs_b = np.array([datapoint[1] for datapoint in b])
        # whistle_b = [datapoint[0] for datapoint in b]
        freqs_b = freqs_b - np.mean(freqs_b[whistle_b])
        # freqs_b = freqs_b - np.mean(np.where(whistle_b, freqs_b))

        d = 0
        # d += np.sum(np.where(np.logical_and(whistle_a,  whistle_b), (freqs_a - freqs_b) ** 2, 0))
        d = whistle_a * freqs_a
        return d

    def update(self, whistle, freq):
        self.whistles.pop(0)
        self.freqs.pop(0)

        self.whistles.append(whistle)
        self.freqs.append(freq)

    def load_data(self, filename):
        self.sample_data = pickle.load(open(filename, 'rb'))
        logging.info("Loaded training data from {}".format(filename))

    def save_data(self, filename):
        pickle.dump(self.sample_data, open(filename, 'wb'))
        logging.info("Saved training data in {}".format(filename))

    def detect_signal(self, sample_freq, sample_whistle):

        # Avoid division by zero warning
        sample_freq = np.where(sample_freq == 0, np.NaN, sample_freq)

        # current_block = []
        # signal = []
        # for i, (val, whistle) in enumerate(zip(np.log2(sample_freq), sample_whistle)):
        #     if len(current_block) == 0:
        #         if whistle:
        #             current_block.append(val)
        #         else:
        #             pass
        #     else:
        #         # Is the frequency roughly the same as the ones before?
        #         if whistle and abs(val - np.mean(current_block)) < 0.03:
        #             current_block.append(val)
        #         else:
        #             # Block finished
        #             if len(current_block) >= 2:
        #                 signal.append(np.mean(current_block))
        #             # variations = np.abs(np.array(current_block) - np.mean(current_block))
        #             # print(f'Variation in block: min={variations.min():.3f}   max={variations.max():.3f}   mean={variations.mean():.3f}')
        #             current_block = []

        # result = ''
        # for i in range(len(signal) - 1):
        #     result += 'H' if signal[i] < signal[i + 1] else 'L'

        # if signal:
        #     print(f"signal: {signal}")

        for signal_key, signal_val in SIGNALS.items():
            whistle_signal_raw = [val for i, (val, whistle) in enumerate(zip(np.log2(sample_freq), sample_whistle)) if whistle]
            if len(whistle_signal_raw) > 2:
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
                            print(f'Overshoot in signal {signal_key}!')
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



        # signal_rel = np.array([val - signal[0] for val in signal])
        # for key, val in SIGNALS.items():
        #     if len(signal_rel) == len(val):
        #         val_rel = np.array([v - val[0] for v in val])
        #         max_diff = np.max(np.abs(signal_rel - val_rel))
        #         print(f'Difference: {signal_rel - val_rel}')
        #         if max_diff < 0.05:
        #             return key, signal

        result = ' '
        # if result in SIGNALS.keys():
        #     return SIGNALS[result], result
            # print(f"Found signal {SIGNALS[result]}")
        return None, result