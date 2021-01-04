import numpy as np
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner

import matplotlib.pyplot as plt
import logging

from pfython import BasePfython, FREQUENCY_RANGE
from detector import Detector

HISTORY_LENGTH = 30

class RecordSamplesPage(BoxLayout):
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
        # Buttons on the left side
        buttons = BoxLayout(orientation='vertical', width=Window.size[0]*0.1, size_hint_x=None)
        self.discard_button = Button(text='Discard\nrecorded\nsample', disabled=True)#, font_size='15sp')
        self.discard_button.bind(on_press=self.discard_sample)
        buttons.add_widget(self.discard_button)

        self.class_dropdown = Spinner(text='Sample\nclass', disabled=True)
        self.class_dropdown.bind(text=self.chose_class_key)
        buttons.add_widget(self.class_dropdown)

        self.save_button = Button(text='Save\nrecorded\nsample', disabled=True)
        self.save_button.bind(on_press=self.save_sample)
        buttons.add_widget(self.save_button)

        lower.add_widget(buttons)

        # Plot of recording
        self.fig = plt.figure()
        lower.add_widget(FigureCanvasKivyAgg(self.fig))

        self.add_widget(lower)

        # History of recorded data (size  <= HIST_LENGTH)
        self.history = []

        self.class_key = None

        self.pause = False

    def update(self, freqs, intensities, signal, whistle, max_freq):
        if self.pause:
            return

        ax = self.fig.gca()

        if len(self.history) >= HISTORY_LENGTH:
            self.history.pop(0)
        self.history.append((whistle, max_freq))

        # Full signal recorded
        if len(self.history) == 30 and self.history[0][0]:
            self.pause = True
            title = 'Signal found. Do you want to keep it?'
        else:
            title = 'Recording ...'

        # Plot current recording
        ax.cla()
        ax.set_ylim(*np.log2(FREQUENCY_RANGE))
        ax.set_xlim(-1, HISTORY_LENGTH)
        for i in range(1, len(self.history)):
            last_whistle, current_whistle = self.history[i - 1][0], self.history[i][0]
            if last_whistle and current_whistle:
                linestyle = '--'
            else:
                linestyle = ''

            ax.plot([i - 1, i], [np.log2(self.history[i - 1][1]), np.log2(self.history[i][1])], linestyle=linestyle, color='b', marker='x')
        ax.set_title(title)
        self.fig.canvas.draw_idle()

    def discard_sample(self, instance):
        self.pause = False
        self.history = []

    def save_sample(self, instance):
        # No class key has been selected. Can't save, do nothing
        # TODO Build a notification
        if self.class_key is None:
            logging.info('No class selected. Done nothing')
            return

        whistles = np.array([i[0] for i in self.history], dtype=bool)
        freqs    = np.array([i[1] for i in self.history])
        self.detector.sample_data[self.class_key].append((freqs, whistles))
        self.detector.save_data(self.file_name.text)
        self.discard_sample(None)

    def chose_class_key(self, spinner, text):
        if text == 'Add class':
            n_classes = len(self.detector.sample_data.keys())
            self.class_key = n_classes
            self.detector.sample_data[self.class_key] = []
        else:
            self.class_key = int(text)
        logging.info('Set class_key to {}'.format(self.class_key))
        self.class_dropdown.values = [str(key) for key in self.detector.sample_data.keys()] + ['Add class']

    def load_from_file(self, instance):
        self.detector.load_data(self.file_name.text)
        self.class_dropdown.values = [str(key) for key in self.detector.sample_data.keys()] + ['Add class']
        self.discard_button.disabled = False
        self.class_dropdown.disabled = False
        self.save_button.disabled = False