import numpy as np
import matplotlib.pyplot as plt
from detector import Detector, OBSERVED_LENGTH
from pfython import FREQUENCY_RANGE

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window
from kivy.uix.textinput import TextInput
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg


class DetectionPage(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.detector = Detector()

        # Horizontal bar to load data on top
        self.load_from_file_widget = GridLayout(cols=3, height=Window.size[1] * 0.05, size_hint_y=None)
        self.load_from_file_widget.add_widget(Label(text='File name:'))
        self.file_name = TextInput(text='train_data')
        self.load_from_file_widget.add_widget(self.file_name)
        self.load_button = Button(text='Load from file')
        self.load_button.bind(on_press=self.load_from_file)
        self.load_from_file_widget.add_widget(self.load_button)
        self.add_widget(self.load_from_file_widget)

        lower = BoxLayout(orientation='horizontal', height=Window.size[1]*0.85, size_hint_y=None)

        # Plot of recording
        self.fig = plt.figure()
        lower.add_widget(FigureCanvasKivyAgg(self.fig))

        self.add_widget(lower)

        # History of recorded data (size  <= OBSERVED_LENGTH)
        self.history = []
        self.current_result = None  # Ignore repetitions

        self.pause = False

    def update(self, freqs, intensities, signal, whistle, max_freq):
        if self.pause:
            return

        ax = self.fig.gca()

        if len(self.history) >= OBSERVED_LENGTH:
            self.history.pop(0)
        self.history.append((whistle, max_freq))

        ax.cla()
        ax.set_ylim(*np.log2(FREQUENCY_RANGE))
        ax.set_xlim(-1, OBSERVED_LENGTH)
        for i in range(1, len(self.history)):
            last_whistle, current_whistle = self.history[i - 1][0], self.history[i][0]
            if last_whistle and current_whistle:
                linestyle = '--'
            else:
                linestyle = ''

            with np.errstate(divide='ignore'):
                ax.plot([i - 1, i], [np.log2(self.history[i - 1][1]), np.log2(self.history[i][1])], linestyle=linestyle, color='b', marker='x')
        # ax.set_title(title)
        self.fig.canvas.draw_idle()

        whistles_live = np.array([i[0] for i in self.history], dtype=bool)
        freqs_live = np.array([i[1] for i in self.history])

        # if len(self.history) < OBSERVED_LENGTH:
        #     return

        result, signal_result = self.detector.detect_signal(freqs_live, whistles_live)
        if not result is None:
            self.history = [(False, 0) for _ in range(OBSERVED_LENGTH)]
        if not self.current_result is None:
            # print('Current result')
            if result is None:
                # print('No current result')
                self.current_result = None
        else:
            # print('No current result', result)
            if not result is None:
                print(f'Found signal {result}')
                self.current_result = result
            else:
                # print(f'Not known, but found {result, signal_result}')
                pass


        # scores = defaultdict(lambda: [])
        # for class_key, class_data in self.detector.sample_data.items():
        #     print(f'Class {class_key}: ', end='')
        #     for freqs, whistle in class_data:
        #         metric = self.detector.compare_blocks(freqs, whistle, freqs_live, whistles_live)
        #         print(f'{metric}  ', end='')
        #         # scores[class_key].append(metric)
        #     print()
        # print()


    def load_from_file(self, instance):
        self.detector.load_data(self.file_name.text)