import csv
import tempfile

import pandas as pd
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QRadioButton,
    QPushButton,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QFrame,
    QSlider,
    QLabel,
    QSizePolicy,
    QSpacerItem,
    QButtonGroup
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, QTimer, Qt
import pyqtgraph as pg
import numpy as np
import wave
import sys
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from scipy.io import wavfile
from PyQt5 import QtGui
from PyQt5 import QtCore
import soundfile as sf
from scipy.signal import spectrogram
from PyQt6.QtCore import QSize


class SignalViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.plot_widget = pg.PlotWidget()
        self.media_player = QMediaPlayer()
        self.needle = pg.InfiniteLine(pos=0, angle=90, movable=False, pen="cyan")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_needle)
        self.plot_item = self.plot_widget.plot(pen=pg.mkPen(color="gray"))
        self.audio_data = None
        self.sample_rate = 0
        self.cine_mode = False
        self.current_position = 0

        self.layout.addWidget(self.plot_widget)
        self.setLayout(self.layout)

    def load_waveform(self, file_path):
        with wave.open(file_path, "rb") as wave_file:
            self.sample_rate = wave_file.getframerate()
            self.audio_data = np.frombuffer(wave_file.readframes(wave_file.getnframes()), dtype=np.int16)
            if not self.cine_mode:
                duration = len(self.audio_data) / self.sample_rate
                x = np.linspace(0, duration / 2, len(self.audio_data))
                self.plot_item.setData(x, self.audio_data)
                self.plot_widget.setXRange(x[0], x[-1])
                self.plot_widget.addItem(self.needle)
            else:
                self.plot_item.setData([], [])

    def play_audio(self):
        self.media_player.play()
        self.timer.start(35)
        if self.cine_mode:
            self.current_position = 0
            self.plot_widget.setXRange(0, 5)
            self.plot_item.setData([], [])
        else:
            duration = len(self.audio_data) / self.sample_rate
            x = np.linspace(0, duration / 2, len(self.audio_data))
            self.plot_item.setData(x, self.audio_data)
            self.plot_widget.setXRange(x[0], x[-1])
            self.plot_widget.addItem(self.needle)

    def update_needle(self):
        if self.media_player.state() == QMediaPlayer.State.PlayingState:
            position = self.media_player.position() / 1000.0
            if self.cine_mode:
                self.update_cine_mode(position)
            else:
                self.needle.setPos(position)

    def update_cine_mode(self, position):
        window_size = 3 
        start_time = max(0, position - window_size)
        end_time = position
        start_index = int(start_time * self.sample_rate*2)
        end_index = int(end_time * self.sample_rate*2)
        y = self.audio_data[start_index:end_index]
        x = np.linspace(start_time, end_time, end_index - start_index)
        self.plot_item.setData(x, y)
        self.update_x_axis(position)

    def update_x_axis(self, position):
        window_size = 3 
        start_time = max(0, position - window_size)
        end_time = start_time + window_size
        self.plot_widget.setXRange(start_time, end_time)

    def pause_audio(self):
        self.media_player.pause()
        self.timer.stop()

    def rewind_audio(self):
        self.media_player.setPosition(0)
        self.media_player.play()
        self.needle.setPos(0)
        self.timer.start(35)

    def forward_audio(self):
        current_position = self.media_player.position()
        new_position = current_position + 200
        self.media_player.setPosition(new_position)

        if self.cine_mode:
            position = new_position / 1000.0
            self.update_cine_mode(position)
        else:
            self.needle.setPos(new_position / 1000.0)

    def backward_audio(self):
        current_position = self.media_player.position()
        new_position = max(0, current_position - 200)
        self.media_player.setPosition(new_position)

        if self.cine_mode:
            position = new_position / 1000.0
            self.update_cine_mode(position)
        else:
            self.needle.setPos(new_position / 1000.0)

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.isCSV = False
        self.audio_data = None
        self.original_magnitudes = None
        self.positive_freqs = None
        self.fft_freq = None
        self.ftt_data = None
        self.setWindowTitle("Simple Signal Viewer")
        self.setGeometry(50, 50, 600, 1000)

        self.current_mode = "Uniform Mode"
        self.freq_data = None
        self.freq_ranges = []
        self.sliders = []
        self.isShown = True

        with open("Style/index.qss", "r") as f:
            self.setStyleSheet(f.read())

        playIcon = QtGui.QIcon()
        playIcon.addPixmap(
            QtGui.QPixmap("Style/icons/play.png"),
            QtGui.QIcon.Mode.Normal,
            QtGui.QIcon.State.On,
        )

        pauseIcon = QtGui.QIcon()
        pauseIcon.addPixmap(
            QtGui.QPixmap("Style/icons/pause.png"),
            QtGui.QIcon.Mode.Normal,
            QtGui.QIcon.State.On,
        )

        rewindIcon = QtGui.QIcon()
        rewindIcon.addPixmap(
            QtGui.QPixmap("Style/icons/rewind.png"),
            QtGui.QIcon.Mode.Normal,
            QtGui.QIcon.State.On,
        )

        forwardIcon = QtGui.QIcon()
        forwardIcon.addPixmap(
            QtGui.QPixmap("Style/icons/forward.png"),
            QtGui.QIcon.Mode.Normal,
            QtGui.QIcon.State.On,
        )

        backwardIcon = QtGui.QIcon()
        backwardIcon.addPixmap(
            QtGui.QPixmap("Style/icons/backward.png"),
            QtGui.QIcon.Mode.Normal,
            QtGui.QIcon.State.On,
        )

        loadIcon = QtGui.QIcon()
        loadIcon.addPixmap(
            QtGui.QPixmap("Style/icons/load.png"),
            QtGui.QIcon.Mode.Normal,
            QtGui.QIcon.State.On,
        )

        self.show_hide_button = QPushButton("Hide spectrogram")
        self.show_hide_button.setObjectName("show_hide_button")
        self.show_hide_button.clicked.connect(self.show_hide_spectrogram)

        self.right_frame = QFrame()
        self.right_layout = QVBoxLayout()
        self.right_frame.setLayout(self.right_layout)

        # Signal viewers
        self.input_viewer = SignalViewer()
        self.output_viewer = SignalViewer()

        # Link input and output viewers
        self.input_viewer.plot_widget.setXLink(self.output_viewer.plot_widget)
        self.input_viewer.plot_widget.setYLink(self.output_viewer.plot_widget)

        # Viewer frame
        self.viewer_frame = QFrame()
        self.viewer_frame.setMaximumHeight(250)
        self.viewer_layout = QHBoxLayout()
        self.viewer_frame.setLayout(self.viewer_layout)
        self.viewer_layout.addWidget(self.input_viewer)
        self.viewer_layout.addWidget(self.output_viewer)

        # Add viewer to right layout
        self.right_layout.addWidget(self.viewer_frame)

        # Control buttons
        self.load_button = QPushButton()
        self.load_button.setIcon(loadIcon)
        self.load_button.setIconSize(QtCore.QSize(24, 24))

        self.play_button = QPushButton()
        self.play_button.setIcon(playIcon)
        self.play_button.setIconSize(QtCore.QSize(20, 20))

        self.pause_button = QPushButton()
        self.pause_button.setIcon(pauseIcon)
        self.pause_button.setIconSize(QtCore.QSize(20, 20))

        self.rewind_button = QPushButton()
        self.rewind_button.setIcon(rewindIcon)
        self.rewind_button.setIconSize(QtCore.QSize(24, 24))

        self.forward_button = QPushButton()
        self.forward_button.setIcon(forwardIcon)
        self.forward_button.setIconSize(QtCore.QSize(20, 20))

        self.backward_button = QPushButton()
        self.backward_button.setIcon(backwardIcon)
        self.backward_button.setIconSize(QtCore.QSize(20, 20))
        self.linear_scale_button = QRadioButton("Linear")
        self.linear_scale_button.setStyleSheet(
            "QRadioButton {font-size: 15px;font-weight: bold}"
        )
        self.audiogram_scale_button = QRadioButton("Audiogram")
        self.audiogram_scale_button.setStyleSheet(
            "QRadioButton {font-size: 15px;font-weight: bold}"
        )

    

        self.load_button.clicked.connect(self.load_file)
        self.play_button.clicked.connect(self.play_audio)
        self.pause_button.clicked.connect(self.pause_audio)
        self.rewind_button.clicked.connect(self.rewind_audio)
        self.forward_button.clicked.connect(self.forward_audio)
        self.backward_button.clicked.connect(self.backward_audio)
        self.linear_scale_button.toggled.connect(self.update_frequency_graph)
        self.audiogram_scale_button.toggled.connect(self.update_frequency_graph)

        # Control layout
        dummy_H = QHBoxLayout()

        control_frame_left = QFrame()
        control_frame_left.setObjectName("control_frame_left")
        dummy_H.addWidget(control_frame_left)
        control_layout_left = QHBoxLayout()
        control_frame_left.setLayout(control_layout_left)

        control_layout_left.addWidget(self.linear_scale_button)
        control_layout_left.addWidget(self.audiogram_scale_button)
        control_layout_left.addWidget(self.show_hide_button)

        # Create button groups
        self.plot_mode_group = QButtonGroup(self)
        self.freq_mode_group = QButtonGroup(self)

        # Add radio buttons for Normal Mode and Cine Mode
        self.normal_mode_button = QRadioButton("Normal Plot")
        self.cine_mode_button = QRadioButton("Cine Plot")
        self.normal_mode_button.setChecked(True)

        self.plot_mode_group.addButton(self.normal_mode_button)
        self.plot_mode_group.addButton(self.cine_mode_button)

        self.freq_mode_group.addButton(self.linear_scale_button)
        self.freq_mode_group.addButton(self.audiogram_scale_button)

        # Connect radio buttons to the method
        self.normal_mode_button.toggled.connect(self.change_plot_mode)
        self.cine_mode_button.toggled.connect(self.change_plot_mode)

        # Add radio buttons to the control layout
        control_layout_left.addWidget(self.normal_mode_button)
        control_layout_left.addWidget(self.cine_mode_button)

        control_frame_center = QFrame()
        dummy_H.addSpacerItem(
            QSpacerItem(0, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        )
        dummy_H.addWidget(control_frame_center)
        dummy_H.addSpacerItem(
            QSpacerItem(240, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )
        control_frame_center.setObjectName("control_frame_center")
        control_frame_center.setMaximumHeight(70)
        control_frame_center.setMinimumHeight(70)
        control_frame_center.setMaximumWidth(750)

        control_layout_center = QHBoxLayout()
        # control_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        control_frame_center.setLayout(control_layout_center)
        control_layout_center.addWidget(self.load_button)
        control_layout_center.addWidget(self.backward_button)
        control_layout_center.addWidget(self.pause_button)
        control_layout_center.addWidget(self.play_button)
        control_layout_center.addWidget(self.forward_button)
        control_layout_center.addWidget(self.rewind_button)

        control_frame_right = QFrame()
        control_frame_right.setObjectName("control_frame_right")
        control_layout_right = QHBoxLayout()

        control_frame_right.setLayout(control_layout_right)

        dummy_H.addWidget(control_frame_right)

        self.right_layout.addLayout(dummy_H)
        self.linear_scale_button.setChecked(True)
        self.freq_frame = QFrame()
        self.freq_frame.setMaximumHeight(250)
        self.freq_layout = QHBoxLayout()
        self.freq_frame.setLayout(self.freq_layout)

        self.freq_plot_widget = pg.PlotWidget()
        self.freq_plot_item = self.freq_plot_widget.plot(pen=pg.mkPen(color="blue"))
        self.freq_layout.addWidget(self.freq_plot_widget)
        self.right_layout.addWidget(self.freq_frame)

        self.slider_layout = QHBoxLayout()
        self.right_layout.addLayout(self.slider_layout)

        self.update_sliders()

        self.spec_frame = QFrame()
        self.spec_frame.setMaximumHeight(250)
        self.spec_layout = QHBoxLayout()
        self.spec_frame.setLayout(self.spec_layout)
        self.spec_plot_figure_1 = Figure()
        self.spec_plot_figure_2 = Figure()
        self.spec_canvas_1 = FigureCanvas(self.spec_plot_figure_1)
        self.spec_canvas_1.setFixedSize(500, 250)
        self.spec_canvas_2 = FigureCanvas(self.spec_plot_figure_2)
        self.spec_canvas_2.setFixedSize(500, 250)
        axis1 = self.spec_plot_figure_1.add_subplot(111)
        axis1.set_title("Signal Spectrogram")
        axis1.set_xlabel("Time [s]")
        axis1.set_ylabel("Frequency [Hz] (scaled to '$\pi$')")
        cbar1 = self.spec_canvas_1.figure.colorbar(mappable=None, ax=axis1)
        cbar1.set_label("Magnitude [dB]")

        axis2 = self.spec_plot_figure_2.add_subplot(111)
        axis2.set_title("Reconstructed Signal Spectrogram")
        axis2.set_xlabel("Time [s]")
        axis2.set_ylabel("Frequency [Hz] (scaled to '$\pi$')")
        cbar2 = self.spec_canvas_2.figure.colorbar(mappable=None, ax=axis2)
        cbar2.set_label("Magnitude [dB]")
        self.spec_layout.addWidget(self.spec_canvas_1)
        self.spec_layout.addWidget(self.spec_canvas_2)
        self.right_layout.addWidget(self.spec_frame)

        self.combo_box = QComboBox()
        self.combo_box.setObjectName("combo_box")
        self.combo_box.setMinimumWidth(200)
        self.combo_box.setMaximumWidth(200)
        self.combo_box.setMinimumHeight(40)
        self.combo_box.setStyleSheet("QComboBox {font-size: 15px;}")
        self.combo_box.addItem("Uniform Mode")
        self.combo_box.addItem("Musical Mode")
        self.combo_box.addItem("Animal Mode")
        self.combo_box.addItem("ECG Abnormalities Mode")
        self.combo_box.currentIndexChanged.connect(self.change_mode)

        control_layout_right.addWidget(self.combo_box)

        # Add checkboxes for input and output
        self.input_checkbox = QCheckBox("Input")
        self.output_checkbox = QCheckBox("Output")
        self.input_checkbox.setChecked(True)
        self.output_checkbox.setChecked(True)
        control_layout_right.addWidget(self.input_checkbox)
        control_layout_right.addWidget(self.output_checkbox)

        # Main layout
        layout = QHBoxLayout()
        # layout.addWidget(self.left_frame)
        layout.addWidget(self.right_frame)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def change_plot_mode(self):
        if self.normal_mode_button.isChecked():
            self.input_viewer.cine_mode = False
            self.output_viewer.cine_mode = False
            self.input_viewer.plot_widget.addItem(self.input_viewer.needle)
            self.output_viewer.plot_widget.addItem(self.output_viewer.needle)
            self.input_viewer.play_audio()
            self.output_viewer.play_audio()
        elif self.cine_mode_button.isChecked():
            self.input_viewer.cine_mode = True
            self.output_viewer.cine_mode = True
            self.input_viewer.plot_widget.removeItem(self.input_viewer.needle)
            self.output_viewer.plot_widget.removeItem(self.output_viewer.needle)
            self.input_viewer.play_audio()
            self.output_viewer.play_audio()
        print('cine_mode:', self.input_viewer.cine_mode)

    def show_hide_spectrogram(self):
        if not self.isShown:
            self.show_hide_button.setText("Hide spectrogram")

            if self.input_viewer.audio_data is not None and self.audio_data is not None:
                self.plot_spectrogram(
                    self.input_viewer.audio_data,
                    self.input_viewer.sample_rate,
                    self.spec_canvas_1,
                    self.spec_plot_figure_1.gca(),
                )
                self.plot_spectrogram(
                    self.audio_data,
                    self.input_viewer.sample_rate,
                    self.spec_canvas_2,
                    self.spec_plot_figure_2.gca(),
                )
            self.spec_frame.show()
        else:
            self.show_hide_button.setText("Show spectrogram")
            self.spec_frame.hide()
        self.isShown = not self.isShown

    def create_sliders(self, slider_num):
        slider_layouts = []
        self.sliders = []
        if self.input_viewer.audio_data is not None:
            min_label, max_label = self.update_frequency_graph()
        else:
            min_label, max_label = 0, 0

        if self.current_mode == "Uniform Mode":
            for i in range(slider_num):

                slider_container = QVBoxLayout()
                slider_container.setAlignment(
                    Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop
                )

                slider = QSlider(Qt.Orientation.Vertical)
                slider.setMinimum(0)
                slider.setMaximum(10)
                slider.setValue(5)
                slider.setTickPosition(QSlider.TicksBothSides)
                slider.setTickInterval(1)

                if i == 0:
                    label = QLabel(f" ({min_label:.1f}, {max_label * (i + 1):.1f}) KHz")
                else:
                    label = QLabel(
                        f" ({max_label * i:.1f}, {max_label * (i + 1):.1f}) KHz"
                    )

                label.setAlignment(Qt.AlignLeft)
                label.setObjectName("slider_label")
                label.setMaximumWidth(200)

                slider_container.addWidget(slider)
                slider_container.addWidget(label)

                slider_layouts.append(slider_container)
                self.sliders.append(slider)
                slider.valueChanged.connect(
                    lambda value, index=i: self.update_frequency_graph(index)
                )
        elif self.current_mode == "Musical Mode":

            freq_labels = ["Trumpet", "Piano and Bass", "Cymbals", "Xylophone"]
            freq_ranges = [(0, 350), (350, 1000), (860, 4000), (4200, 22000)]

            for i in range(slider_num):
                slider_container = QVBoxLayout()

                slider = QSlider(Qt.Orientation.Vertical)
                slider.setMinimum(0)
                slider.setMaximum(10)
                slider.setValue(5)
                slider.setTickPosition(QSlider.TicksBothSides)
                slider.setTickInterval(1)

                label = QLabel(
                    f"{freq_labels[i]} ({freq_ranges[i][0] / 1000:.1f}, {freq_ranges[i][1] / 1000:.1f}) KHz"
                )
                label.setAlignment(Qt.AlignLeft)
                label.setObjectName("slider_label")
                if i == 0:
                    label.setMaximumWidth(127)
                elif i == 1:
                    label.setMaximumWidth(210)
                elif i == 2:
                    label.setMaximumWidth(147)
                elif i == 3:
                    label.setMaximumWidth(165)
                slider_container.addWidget(slider)
                slider_container.addWidget(label)

                slider_layouts.append(slider_container)
                self.sliders.append(slider)
                slider.valueChanged.connect(
                    lambda value, index=i: self.update_frequency_graph(index)
                )

        elif self.current_mode == "Animal Mode":

            freq_labels = ["Whale", "Dog", "Cricket", "Bat"]
            freq_ranges = [0, 500], [500, 1500], [1500, 4500], [4500, 12000]

            for i in range(slider_num):
                slider_container = QVBoxLayout()

                slider = QSlider(Qt.Orientation.Vertical)
                slider.setMinimum(0)
                slider.setMaximum(10)
                slider.setValue(5)
                slider.setTickPosition(QSlider.TicksBothSides)
                slider.setTickInterval(1)

                label = QLabel(
                    f"{freq_labels[i]} ({freq_ranges[i][0] / 1000:.1f}, {freq_ranges[i][1] / 1000:.1f}) KHz"
                )
                label.setAlignment(Qt.AlignLeft)
                label.setMaximumWidth(140)
                slider_container.addWidget(slider)
                slider_container.addWidget(label)

                slider_layouts.append(slider_container)
                self.sliders.append(slider)
                slider.valueChanged.connect(
                    lambda value, index=i: self.update_frequency_graph(index)
                )
        elif self.current_mode == "ECG Abnormalities Mode":

            freq_labels = ["Normal", "T1", "T1", "T1"]
            freq_ranges = [0, 100], [100, 350], [300, 450], [400, 500]

            for i in range(slider_num):
                slider_container = QVBoxLayout()

                slider = QSlider(Qt.Orientation.Vertical)
                slider.setMinimum(0)
                slider.setMaximum(10)
                slider.setValue(5)
                slider.setTickPosition(QSlider.TicksBothSides)
                slider.setTickInterval(1)

                label = QLabel(
                    f"{freq_labels[i]} ({freq_ranges[i][0] / 1000:.1f}, {freq_ranges[i][1] / 1000:.1f}) KHz"
                )
                label.setAlignment(Qt.AlignLeft)
                label.setMaximumWidth(140)
                slider_container.addWidget(slider)
                slider_container.addWidget(label)

                slider_layouts.append(slider_container)
                self.sliders.append(slider)
                slider.valueChanged.connect(
                    lambda value, index=i: self.update_frequency_graph(index)
                )
        return slider_layouts

    def change_mode(self, index):
        self.current_mode = self.combo_box.itemText(index)
        self.update_sliders()
        self.reset_sliders()
        print(self.current_mode)

    def update_sliders(self):

        for i in reversed(range(self.slider_layout.count())):
            widget_to_remove = self.slider_layout.itemAt(i).layout()
            if widget_to_remove:
                while widget_to_remove.count():
                    item = widget_to_remove.takeAt(0)
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()
                self.slider_layout.removeItem(widget_to_remove)

        slider_num = 10 if self.current_mode == "Uniform Mode" else 4
        slider_layouts = self.create_sliders(slider_num)
        for slider_layout in slider_layouts:
            self.slider_layout.addLayout(slider_layout)

    def load_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "WAV Files (*.wav);;CSV Files (*.csv);;All Files (*)",
            options=options,
        )

        if file_path:
            self.reset_viewers()
            if file_path.endswith(".csv"):
                self.isCSV = True
                wav_file_path = self.convert_csv_to_wav(file_path)
                self.input_viewer.load_waveform(wav_file_path)
                self.input_viewer.media_player.setMedia(
                    QMediaContent(QUrl.fromLocalFile(wav_file_path))
                )
            elif file_path.endswith(".wav"):
                self.isCSV = False
                self.input_viewer.load_waveform(file_path)
                self.input_viewer.media_player.setMedia(
                    QMediaContent(QUrl.fromLocalFile(file_path))
                )

            # Ensure fft is called to initialize original_magnitudes
            (
                self.ftt_data,
                self.fft_freq,
                self.positive_freqs,
                self.original_magnitudes,
            ) = self.fft()

            if not self.cine_mode_button.isChecked():
                self.output_viewer.plot_widget.addItem(self.output_viewer.needle)
                self.input_viewer.plot_widget.addItem(self.input_viewer.needle)

            self.update_sliders()
            self.update_frequency_graph()
            self.reset_sliders()

            if self.input_viewer.audio_data is not None:
                self.plot_output(self.input_viewer.audio_data)
                if self.isShown:
                    self.plot_spectrogram(
                        self.input_viewer.audio_data,
                        self.input_viewer.sample_rate,
                        self.spec_canvas_1,
                        self.spec_plot_figure_1.gca(),
                    )
            self.update_frequency_graph()
            self.play_audio()
            return (
                self.ftt_data,
                self.fft_freq,
                self.positive_freqs,
                self.original_magnitudes,
            )

    def convert_csv_to_wav(self, file_path, sample_rate=44100):
        data = pd.read_csv(file_path, header=None)

        # Check if the CSV file has two columns
        if data.shape[1] == 2:
            # Select only the second column
            samples = data.iloc[:, 1].values
        else:
            samples = data.values.flatten()

        samples = samples / np.max(np.abs(samples)) * 32767
        samples = samples.astype(np.int16)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            wav_file = temp_file.name
        wavfile.write(wav_file, sample_rate, samples)
        return wav_file

    def plot_output(self, output_data):
        self.output_viewer.audio_data = output_data
        self.output_viewer.sample_rate = self.input_viewer.sample_rate

        if self.cine_mode_button.isChecked():
            self.output_viewer.cine_mode = True
            self.output_viewer.plot_item.setData([], [])
        else:
            self.output_viewer.cine_mode = False
            duration = (len(output_data) / self.input_viewer.sample_rate)
            x = np.linspace(0, duration / 2, len(output_data))
            self.output_viewer.plot_item.setData(x, output_data)
            self.output_viewer.plot_widget.setXRange(x[0], x[-1])
            self.output_viewer.plot_widget.addItem(self.output_viewer.needle)

        self.output_viewer.media_player.stop()

        self.audio_data = output_data.astype(np.int16)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            output_file_path = temp_file.name
            wavfile.write(
                output_file_path, self.input_viewer.sample_rate * 2, self.audio_data
            )

        self.output_viewer.media_player.setMedia(
            QMediaContent(QUrl.fromLocalFile(output_file_path))
        )
        if self.isShown:
            self.plot_spectrogram(
                self.audio_data,
                self.input_viewer.sample_rate,
                self.spec_canvas_2,
                self.spec_plot_figure_2.gca(),
            )

    def fft(self):
        self.ftt_data = np.fft.fft(self.input_viewer.audio_data)
        self.fft_freq = np.fft.fftfreq(
            len(self.ftt_data), 1 / self.input_viewer.sample_rate
        )
        self.positive_freqs = self.fft_freq[: len(self.fft_freq) // 2]
        self.original_magnitudes = np.abs(self.ftt_data[: len(self.ftt_data) // 2])
        return (
            self.ftt_data,
            self.fft_freq,
            self.positive_freqs,
            self.original_magnitudes,
        )

    def update_frequency_graph(self, index=None):
        if self.input_viewer.audio_data is not None:
            if not hasattr(self, "original_magnitudes") or index is None:
                if not hasattr(self, "ftt_data") or not hasattr(self, "fft_freq"):
                    (
                        self.ftt_data,
                        self.fft_freq,
                        self.positive_freqs,
                        self.original_magnitudes,
                    ) = self.fft()
                self.modified_magnitudes = self.original_magnitudes.copy()
                self.slider_label_min = self.positive_freqs[0] / 1000
                self.slider_label_max = (self.positive_freqs[-1] - self.positive_freqs[0]) / 10000

            if index is not None:
                slider = self.sliders[index]
                labels = slider.parent().findChildren(QLabel)
                label_text = labels[index].text()
                freq_range_text = label_text.split("(")[-1].strip(") KHz")
                min_freq, max_freq = map(float, freq_range_text.split(","))
                min_freq *= 1000
                max_freq *= 1000
                if self.audiogram_scale_button.isChecked():
                    magnitudes_db = 20 * np.log10(self.modified_magnitudes)
                    self.freq_plot_item.setData(self.positive_freqs, magnitudes_db)
                    self.freq_plot_widget.getPlotItem().invertY(True)
                    self.freq_plot_widget.setLabel("left", "H L (dB)")
                else:
                    self.freq_plot_item.setData(
                        self.positive_freqs, self.modified_magnitudes
                    )
                    self.freq_plot_widget.getPlotItem().invertY(False)
                    self.freq_plot_widget.setLabel("left", "Magnitude")

                if slider.value() != 0:
                    gain = 1 + (slider.value() - 5) * 0.5
                    freq_range = np.where(
                        (self.positive_freqs >= min_freq)
                        & (self.positive_freqs < max_freq)
                    )[0]

                    self.modified_magnitudes[freq_range] = (
                            self.original_magnitudes[freq_range] * gain
                    )

                    temp_ftt_data = self.ftt_data.copy()
                    half_len = len(temp_ftt_data) // 2
                    temp_ftt_data[:half_len] = self.modified_magnitudes * np.exp(
                        1j * np.angle(temp_ftt_data[:half_len])
                    )
                    temp_ftt_data[half_len + 1:] = np.conj(
                        temp_ftt_data[1:half_len][::-1]
                    )

                    reconstructed_signal = np.fft.ifft(temp_ftt_data).real
                    self.plot_output(reconstructed_signal)

                else:

                    freq_range = np.where(
                        (self.positive_freqs >= min_freq)
                        & (self.positive_freqs < max_freq)
                    )[0]
                    self.modified_magnitudes[freq_range] = 0

                    # Use original FTT data as base for zeroed adjustment
                    temp_ftt_data = self.ftt_data.copy()
                    half_len = len(temp_ftt_data) // 2
                    temp_ftt_data[:half_len] = self.modified_magnitudes * np.exp(
                        1j * np.angle(temp_ftt_data[:half_len])
                    )
                    temp_ftt_data[half_len + 1:] = np.conj(
                        temp_ftt_data[1:half_len][::-1]
                    )
                    reconstructed_signal = np.fft.ifft(temp_ftt_data).real
                    self.plot_output(reconstructed_signal)

            print(self.isCSV)
            if self.isCSV:
                if self.current_mode == "Uniform Mode":
                    plot_freq = 2500
                else:
                    plot_freq = 500
                mask = (self.positive_freqs <= plot_freq)
                masked_pos_freq = self.positive_freqs[mask]
                masked_mod_mag = self.modified_magnitudes[mask]
                self.slider_label_min = masked_pos_freq[0] / 1000
                self.slider_label_max = (masked_pos_freq[-1] - masked_pos_freq[0]) / 10000
                self.freq_plot_item.setData(masked_pos_freq, masked_mod_mag)

            else:
                self.freq_plot_item.setData(self.positive_freqs, self.modified_magnitudes)

            return self.slider_label_min, self.slider_label_max

    def plot_spectrogram(self, amplitude, sample_rate, figure, axis):
        frequencies, times, amplitudes = spectrogram(amplitude, sample_rate)
        frequencies = frequencies * np.pi / np.max(frequencies)
        axis.pcolormesh(
            times, frequencies, 10 * np.log10(amplitudes + 1e-10), shading="gouraud"
        )
        figure.draw()

    def reset_viewers(self):
        self.input_viewer.plot_item.clear()
        self.output_viewer.plot_item.clear()
        self.input_viewer.media_player.stop()
        self.output_viewer.media_player.stop()
        self.input_viewer.needle.setPos(0)
        self.output_viewer.needle.setPos(0)
        self.input_viewer.audio_data = None
        self.output_viewer.audio_data = None

    def reset_sliders(self):
        for slider in self.sliders:
            slider.setValue(5)

    def csv_exporter(self, file_name, input_file):

        with open(file_name, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow((["Frequency"]))
            # Write each item in the list to a new row
            for row1 in input_file:
                writer.writerow([row1])

    def play_audio(self):
        if self.input_checkbox.isChecked():
            self.input_viewer.play_audio()
            self.input_viewer.timer.start(35)
        if self.output_checkbox.isChecked():
            self.output_viewer.play_audio()
        self.output_viewer.timer.start(35)

    def pause_audio(self):
        self.input_viewer.pause_audio()
        self.output_viewer.pause_audio()

    def rewind_audio(self):
        if self.input_checkbox.isChecked():
            self.input_viewer.rewind_audio()
            self.input_viewer.timer.start(35)
        if self.output_checkbox.isChecked():
            self.output_viewer.rewind_audio()
        self.output_viewer.timer.start(35)

    def forward_audio(self):
        self.input_viewer.forward_audio()
        self.output_viewer.forward_audio()

    def backward_audio(self):
        self.input_viewer.backward_audio()
        self.output_viewer.backward_audio()


def main():
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
