import tempfile

import sounddevice as sd
import csv
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QCheckBox, QComboBox, \
    QFileDialog, \
    QHBoxLayout, QFrame, QSlider, QLabel, QSizePolicy
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, QTimer, Qt
import pyqtgraph as pg
import numpy as np
import wave
import sys
import soundfile as sf
from scipy.io import wavfile


class SignalViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.plot_widget = pg.PlotWidget()
        self.media_player = QMediaPlayer()
        self.needle = pg.InfiniteLine(pos=0, angle=90, movable=False, pen='cyan')
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_needle)
        self.plot_item = self.plot_widget.plot(pen=pg.mkPen(color='gray'))
        self.audio_data = None
        self.sample_rate = 0

        self.layout.addWidget(self.plot_widget)
        self.setLayout(self.layout)

    def load_waveform(self, file_path):
        with wave.open(file_path, 'rb') as wave_file:
            self.sample_rate = wave_file.getframerate()
            self.audio_data = np.frombuffer(wave_file.readframes(-1), dtype=np.int16)
            duration = (len(self.audio_data) / self.sample_rate) / 2
            x = np.linspace(0, duration, len(self.audio_data))
            self.plot_item.setData(x, self.audio_data)
            self.plot_widget.setXRange(x[0], x[-1])
            self.plot_widget.addItem(self.needle)

    def play_audio(self):
        self.media_player.play()
        self.timer.start(35)

    def update_needle(self):
        if self.media_player.state() == QMediaPlayer.State.PlayingState:
            position = self.media_player.position() / 1000.0
            self.needle.setPos(position)

    def pause_audio(self):
        self.media_player.pause()
        self.timer.stop()

    def rewind_audio(self):
        self.media_player.setPosition(0)
        self.media_player.play()
        self.needle.setPos(0)
        self.timer.start(35)

    def forward_audio(self):
        was_playing = self.media_player.state() == QMediaPlayer.State.PlayingState
        self.pause_audio()
        current_position = self.media_player.position()
        self.media_player.setPosition(current_position + 1000)
        if was_playing:
            self.play_audio()

    def backward_audio(self):
        was_playing = self.media_player.state() == QMediaPlayer.State.PlayingState
        self.pause_audio()
        current_position = self.media_player.position()
        self.media_player.setPosition(max(0, current_position - 1000))
        if was_playing or self.media_player.state() == QMediaPlayer.State.StoppedState:
            self.play_audio()


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Signal Viewer")
        self.setGeometry(100, 100, 800, 600)

        self.current_mode = 'Uniform Mode'
        self.freq_data = None
        self.freq_ranges = []
        self.sliders = []

        # Left side (controls, combo box)
        self.left_frame = QFrame()
        self.left_frame.setMaximumWidth(400)
        self.left_frame.setMinimumWidth(400)
        self.left_layout = QVBoxLayout()
        self.left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.left_frame.setLayout(self.left_layout)

        # Right side (viewer, sliders, etc.)
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
        self.load_button = QPushButton("Load WAV File")
        self.play_button = QPushButton("Play")
        self.pause_button = QPushButton("Pause")
        self.rewind_button = QPushButton("Rewind")
        self.forward_button = QPushButton("Forward")
        self.backward_button = QPushButton("Backward")

        self.load_button.clicked.connect(self.load_file)
        self.play_button.clicked.connect(self.play_audio)
        self.pause_button.clicked.connect(self.pause_audio)
        self.rewind_button.clicked.connect(self.rewind_audio)
        self.forward_button.clicked.connect(self.forward_audio)
        self.backward_button.clicked.connect(self.backward_audio)

        # Control layout
        control_layout = QHBoxLayout()
        control_layout.addWidget(self.load_button)
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.pause_button)
        control_layout.addWidget(self.rewind_button)
        control_layout.addWidget(self.forward_button)
        control_layout.addWidget(self.backward_button)

        self.right_layout.addLayout(control_layout)


        self.freq_frame = QFrame()
        self.freq_frame.setMaximumHeight(250)
        self.freq_layout = QHBoxLayout()
        self.freq_frame.setLayout(self.freq_layout)

        self.freq_plot_widget = pg.PlotWidget()
        self.freq_plot_item = self.freq_plot_widget.plot(pen=pg.mkPen(color='blue'))
        self.freq_layout.addWidget(self.freq_plot_widget)
        self.right_layout.addWidget(self.freq_frame)

        self.slider_layout = QHBoxLayout()
        self.right_layout.addLayout(self.slider_layout)

        self.update_sliders()

        self.spec_frame = QFrame()
        self.spec_frame.setMaximumHeight(250)
        self.spec_layout = QHBoxLayout()
        self.spec_frame.setLayout(self.spec_layout)
        self.spec_plot_widget_1 = pg.PlotWidget()
        self.spec_plot_widget_2 = pg.PlotWidget()
        self.spec_layout.addWidget(self.spec_plot_widget_1)
        self.spec_layout.addWidget(self.spec_plot_widget_2)
        self.right_layout.addWidget(self.spec_frame)

        self.combo_box = QComboBox()
        self.combo_box.addItem('Uniform Mode')
        self.combo_box.addItem('Musical Mode')
        self.combo_box.addItem('Animal Mode')
        self.combo_box.addItem('ECG Abnormalities Mode')
        self.combo_box.currentIndexChanged.connect(self.change_mode)
        self.left_layout.addWidget(self.combo_box)

        # Add checkboxes for input and output
        self.input_checkbox = QCheckBox("Play Input")
        self.output_checkbox = QCheckBox("Play Output")
        self.input_checkbox.setChecked(True)
        self.output_checkbox.setChecked(True)
        self.left_layout.addWidget(self.input_checkbox)
        self.left_layout.addWidget(self.output_checkbox)

        # Main layout
        layout = QHBoxLayout()
        layout.addWidget(self.left_frame)
        layout.addWidget(self.right_frame)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

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

                slider = QSlider(Qt.Orientation.Vertical)
                slider.setMinimum(0)
                slider.setMaximum(10)
                slider.setValue(5)
                slider.setTickPosition(QSlider.TicksBothSides)
                slider.setTickInterval(1)

                if i == 0:
                    label = QLabel(f" ({min_label:.1f}, {max_label * (i + 1):.1f}) KHz")
                else:
                    label = QLabel(f" ({max_label * i:.1f}, {max_label * (i + 1):.1f}) KHz")

                label.setAlignment(Qt.AlignLeft)

                slider_container.addWidget(slider)
                slider_container.addWidget(label)

                slider_layouts.append(slider_container)
                self.sliders.append(slider)
                slider.valueChanged.connect(lambda value, index=i: self.update_frequency_graph(index))
        elif self.current_mode == "Musical Mode":

            freq_labels = ["Bass", "Trumpet", "Drums", "Violin"]
            freq_ranges = [(0, 200), (200, 2000), (2000, 4000), (4000, 14000)]

            for i in range(slider_num):
                slider_container = QVBoxLayout()

                slider = QSlider(Qt.Orientation.Vertical)
                slider.setMinimum(0)
                slider.setMaximum(10)
                slider.setValue(5)
                slider.setTickPosition(QSlider.TicksBothSides)
                slider.setTickInterval(1)

                label = QLabel(f"{freq_labels[i]} ({freq_ranges[i][0] / 1000:.1f}, {freq_ranges[i][1] / 1000:.1f}) KHz")
                label.setAlignment(Qt.AlignLeft)

                slider_container.addWidget(slider)
                slider_container.addWidget(label)

                slider_layouts.append(slider_container)
                self.sliders.append(slider)
                slider.valueChanged.connect(lambda value, index=i: self.update_frequency_graph(index))
        elif self.current_mode == "Animal Mode":

            freq_labels = ["Whale", "Dog", "Cricket", "Bat"]
            freq_ranges = [0, 500], [500, 1900], [1900, 2900], [8000, 22000]

            for i in range(slider_num):
                slider_container = QVBoxLayout()

                slider = QSlider(Qt.Orientation.Vertical)
                slider.setMinimum(0)
                slider.setMaximum(10)
                slider.setValue(5)
                slider.setTickPosition(QSlider.TicksBothSides)
                slider.setTickInterval(1)

                label = QLabel(f"{freq_labels[i]} ({freq_ranges[i][0] / 1000:.1f}, {freq_ranges[i][1] / 1000:.1f}) KHz")
                label.setAlignment(Qt.AlignLeft)

                slider_container.addWidget(slider)
                slider_container.addWidget(label)

                slider_layouts.append(slider_container)
                self.sliders.append(slider)
                slider.valueChanged.connect(lambda value, index=i: self.update_frequency_graph(index))
        elif self.current_mode == "ECG Abnormalities Mode":
            for i in range(slider_num):

                slider_container = QVBoxLayout()

                slider = QSlider(Qt.Orientation.Vertical)
                slider.setMinimum(0)
                slider.setMaximum(10)
                slider.setValue(5)
                slider.setTickPosition(QSlider.TicksBothSides)
                slider.setTickInterval(1)

                if i == 0:
                    label = QLabel(f" ({min_label:.1f}, {max_label * (i + 1):.1f}) KHz")
                else:
                    label = QLabel(f" ({max_label * i:.1f}, {max_label * (i + 1):.1f}) KHz")

                label.setAlignment(Qt.AlignLeft)

                slider_container.addWidget(slider)
                slider_container.addWidget(label)

                slider_layouts.append(slider_container)
                self.sliders.append(slider)
                slider.valueChanged.connect(self.update_frequency_graph)

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

        slider_num = 10 if self.current_mode == 'Uniform Mode' else 4
        slider_layouts = self.create_sliders(slider_num)
        for slider_layout in slider_layouts:
            self.slider_layout.addLayout(slider_layout)

    def load_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Open WAV File", "", "WAV Files (*.wav);;All Files (*)",
                                                   options=options)
        if file_path:
            self.reset_viewers()
            self.input_viewer.load_waveform(file_path)
            self.input_viewer.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
            self.output_viewer.plot_widget.addItem(self.output_viewer.needle)
            self.update_sliders()
            self.reset_sliders()
            self.update_frequency_graph()
            self.plot_output(self.input_viewer.audio_data)

    def plot_output(self, output_data):
        if self.input_viewer.audio_data is not None:
            duration = (len(output_data) / self.input_viewer.sample_rate) / 2
            x = np.linspace(0, duration, len(output_data))
            self.output_viewer.plot_item.setData(x, output_data)
            self.output_viewer.plot_widget.setXRange(x[0], x[-1])

            self.output_viewer.media_player.stop()

            audio_data = output_data.astype(np.int16)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                output_file_path = temp_file.name
                wavfile.write(output_file_path, self.input_viewer.sample_rate * 2, audio_data)

            self.output_viewer.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(output_file_path)))

    def update_frequency_graph(self, index=None):
        temp_mag = False
        if self.input_viewer.audio_data is not None:
            if not hasattr(self, 'original_magnitudes') or index is None:
                self.ftt_data = np.fft.fft(self.input_viewer.audio_data)
                self.fft_freq = np.fft.fftfreq(len(self.ftt_data), 1 / self.input_viewer.sample_rate)
                self.positive_freqs = self.fft_freq[:len(self.fft_freq) // 2]
                self.original_magnitudes = np.abs(self.ftt_data[:len(self.ftt_data) // 2])
                self.modified_magnitudes = self.original_magnitudes.copy()
                self.slider_label_min = self.positive_freqs[0] / 1000
                self.slider_label_max = (self.positive_freqs[-1] - self.positive_freqs[0]) / 10000

            if index is not None:
                slider = self.sliders[index]
                labels = slider.parent().findChildren(QLabel)
                label_text = labels[index].text()
                freq_range_text = label_text.split('(')[-1].strip(') KHz')
                min_freq, max_freq = map(float, freq_range_text.split(','))
                min_freq *= 1000
                max_freq *= 1000

                if slider.value() != 0:
                    temp_mag = False
                    gain = 1 + (slider.value() - 5) * 0.2
                    freq_range = np.where((self.positive_freqs >= min_freq) & (self.positive_freqs < max_freq))[0]
                    self.modified_magnitudes[freq_range] = self.original_magnitudes[freq_range] * gain

                    half_len = len(self.ftt_data) // 2
                    self.ftt_data[:half_len] = self.modified_magnitudes * np.exp(
                        1j * np.angle(self.ftt_data[:half_len]))
                    self.ftt_data[half_len + 1:] = np.conj(self.ftt_data[1:half_len][::-1])

                    reconstructed_signal = np.fft.ifft(self.ftt_data).real
                    self.plot_output(reconstructed_signal)

                else:
                    temp_mag = True
                    self.temp_magnitudes = self.modified_magnitudes.copy()
                    freq_range = np.where((self.positive_freqs >= min_freq) & (self.positive_freqs < max_freq))[0]
                    self.temp_magnitudes[freq_range] = 0

                    # Reconstruct the signal temporarily
                    temp_ftt_data = self.ftt_data.copy()
                    half_len = len(temp_ftt_data) // 2
                    temp_ftt_data[:half_len] = self.temp_magnitudes * np.exp(1j * np.angle(self.ftt_data[:half_len]))
                    temp_ftt_data[half_len + 1:] = np.conj(temp_ftt_data[1:half_len][::-1])
                    reconstructed_signal = np.fft.ifft(temp_ftt_data).real
                    self.plot_output(reconstructed_signal)
            if temp_mag:
                self.freq_plot_item.setData(self.positive_freqs, self.temp_magnitudes)
            else:
                self.freq_plot_item.setData(self.positive_freqs, self.modified_magnitudes)

            return self.slider_label_min, self.slider_label_max

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
        if self.output_checkbox.isChecked():
            self.output_viewer.play_audio()
        self.input_viewer.timer.start(35)
        self.output_viewer.timer.start(35)

    def pause_audio(self):
        self.input_viewer.pause_audio()
        self.output_viewer.pause_audio()

    def rewind_audio(self):
        if self.input_checkbox.isChecked():
            self.input_viewer.rewind_audio()
        if self.output_checkbox.isChecked():
            self.output_viewer.rewind_audio()
        self.input_viewer.timer.start(35)
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
