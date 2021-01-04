import kivy
from kivy.app import App
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
from detection_page import DetectionPage
from record_samples import RecordSamplesPage

kivy.require("1.11.0")
# logger = logging.Logger('Interface')
logging.basicConfig(format='Interface')

class LivePlotsPage(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.log_scale = False

        self.cols = 1
        # self.rows = 2

        self.log_button = Button(text='Toggle log scale', height=Window.size[1]*0.1, size_hint_y=None)
        self.log_button.bind(on_press=self.toggle_log_scale)
        self.add_widget(self.log_button)

        self.fig = plt.figure()
        self.ax1 = self.fig.add_subplot(211)
        self.ax2 = self.fig.add_subplot(212)
        self.add_widget(FigureCanvasKivyAgg(self.fig))

    def toggle_log_scale(self, *args):
        print(f'Additional arguments in toggle_log_scale: {args}')
        self.log_scale = not self.log_scale

    def update(self, freqs, intensities, signal, whistle, max_freq):
        self.ax1.cla()
        self.ax1.set_ylim(1, 3e6)
        self.ax1.set_xlim(500, 3000)
        self.ax1.grid()
        # ax1.set_xscale('log', basex=2)
        if whistle:
            self.ax1.axvline(max_freq, linestyle='--')
        self.ax1.plot(freqs, intensities)

        if max_freq > 0:
            self.ax1.text(max_freq + 50, max(intensities) + 250000, f'{max_freq:.3f} Hz', verticalalignment='top', fontsize=14)

        if self.log_scale:
            self.ax1.set_yscale('log')

        self.ax2.cla()
        self.ax2.plot(signal)
        self.ax2.set_ylim(-5000, 5000)
        self.fig.canvas.draw_idle()


class ViewSamplesPage(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.detector = Detector()

        self.class_key = None
        self.instance_key = None

        self.load_from_file_widget = GridLayout(cols=3, height=Window.size[1]*0.05, size_hint_y=None)
        self.load_from_file_widget.add_widget(Label(text='File name:'))
        self.file_name = TextInput(text='train_data')
        self.load_from_file_widget.add_widget(self.file_name)
        self.load_button = Button(text='Load from file')
        self.load_button.bind(on_press=self.load_from_file)
        self.load_from_file_widget.add_widget(self.load_button)
        self.add_widget(self.load_from_file_widget)

        dropdowns = BoxLayout(orientation='horizontal', height=Window.size[1]*0.1, size_hint_y=None)
        dropdowns.add_widget(Label(text='Sample class:'))
        self.class_dropdown = Spinner(text='Select class', width=Window.size[0]*0.15, size_hint_x=None)
        self.class_dropdown.bind(text=self.chose_class_key)
        dropdowns.add_widget(self.class_dropdown)

        dropdowns.add_widget(Label(text='Instance in class:'))
        self.instance_dropdown = Spinner(text='Select instance', width=Window.size[0]*0.15, size_hint_x=None)
        self.instance_dropdown.bind(text=self.chose_instance_key)
        dropdowns.add_widget(self.instance_dropdown)

        self.add_widget(dropdowns)

        self.fig = plt.figure()
        self.add_widget(FigureCanvasKivyAgg(self.fig))

    def chose_class_key(self, spinner, text):
        self.class_key = int(text)
        logging.info('Set class_key to {}'.format(self.class_key))
        self.instance_dropdown.values = [str(i) for i in range(len(self.detector.sample_data[self.class_key]))]

    def chose_instance_key(self, spinner, text):
        self.instance_key = int(text)
        logging.info("Selected instance_key {}".format(self.instance_key))
        ax = self.fig.gca()
        ax.cla()
        ax.set_ylim(*FREQUENCY_RANGE)

        freqs, whistles = self.detector.sample_data[self.class_key][self.instance_key]
        for i in range(1, len(freqs)):
            last_whistle, current_whistle = whistles[i - 1], whistles[i]
            if last_whistle and current_whistle:
                linestyle = '--'
            else:
                linestyle = ''

            ax.plot([i - 1, i], [freqs[i - 1], freqs[i]], linestyle=linestyle, color='b', marker='x')
        self.fig.canvas.draw_idle()


    def load_from_file(self, instance):
        self.detector.load_data(self.file_name.text)
        self.class_dropdown.values = [str(key) for key in self.detector.sample_data.keys()]




class PfythonInterface(App):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source = BasePfython()
        self.state = 'LivePlots'

        Clock.schedule_interval(self.update, 0.005)


    def state_button_press(self, instance):
        self.state = instance.text
        self.screen_manager.current = self.state
        logging.info("Switched to state {}".format(self.state))


    def new_screen(self, name, content):
        navigation = BoxLayout(orientation='horizontal', height=Window.size[1]*0.05, size_hint_y=None)

        liveplots_button = Button(text='LivePlots')
        liveplots_button.bind(on_press=self.state_button_press)
        navigation.add_widget(liveplots_button)

        viewsamples_button = Button(text='ViewSamples')
        viewsamples_button.bind(on_press=self.state_button_press)
        navigation.add_widget(viewsamples_button)

        recordsamples_button = Button(text='RecordSamples')
        recordsamples_button.bind(on_press=self.state_button_press)
        navigation.add_widget(recordsamples_button)

        detection_button = Button(text='Detection')
        detection_button.bind(on_press=self.state_button_press)
        navigation.add_widget(detection_button)

        screen = Screen(name=name)
        everything = BoxLayout(orientation='vertical')
        everything.add_widget(navigation)
        everything.add_widget(content)
        screen.add_widget(everything)
        self.screen_manager.add_widget(screen)


    def build(self):
        self.screen_manager = ScreenManager()

        self.liveplots_page = LivePlotsPage()
        self.new_screen(name='LivePlots', content=self.liveplots_page)

        self.viewsamples_page = ViewSamplesPage()
        self.new_screen(name='ViewSamples', content=self.viewsamples_page)

        self.record_samples_page = RecordSamplesPage()
        self.new_screen(name='RecordSamples', content=self.record_samples_page)

        self.detection_page = DetectionPage()
        self.new_screen(name='Detection', content=self.detection_page)

        return self.screen_manager

    def update(self, dtime):
        if self.state == 'LivePlots':
            freqs, intensities, signal = self.source.read_input()
            whistle, max_freq = self.source.analyse_input(freqs, intensities)
            self.liveplots_page.update(freqs, intensities, signal, whistle, max_freq)

        if self.state == 'RecordSamples':
            freqs, intensities, signal = self.source.read_input()
            whistle, max_freq = self.source.analyse_input(freqs, intensities)
            self.record_samples_page.update(freqs, intensities, signal, whistle, max_freq)

        if self.state == 'Detection':
            freqs, intensities, signal = self.source.read_input()
            whistle, max_freq = self.source.analyse_input(freqs, intensities)
            self.detection_page.update(freqs, intensities, signal, whistle, max_freq)


if __name__ == '__main__':
    PfythonInterface().run()