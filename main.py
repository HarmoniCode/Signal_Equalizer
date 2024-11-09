import csv

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QComboBox, QFileDialog, \
    QHBoxLayout, QFrame, QSlider
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, QTimer, Qt
import pyqtgraph as pg
import numpy as np
import wave
import sys


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

        self.left_frame = QFrame()
        self.left_frame.setMaximumWidth(400)
        self.left_frame.setMinimumWidth(400)
        self.left_layout = QVBoxLayout()
        self.left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.left_frame.setLayout(self.left_layout)

        self.right_frame = QFrame()
        self.right_layout = QVBoxLayout()
        self.right_frame.setLayout(self.right_layout)

        self.input_viewer = SignalViewer()
        self.output_viewer = SignalViewer()

        self.input_viewer.plot_widget.setXLink(self.output_viewer.plot_widget)
        self.input_viewer.plot_widget.setYLink(self.output_viewer.plot_widget)

        self.viewer_frame = QFrame()
        self.viewer_frame.setMaximumHeight(250)
        self.viewer_layout = QHBoxLayout()
        self.viewer_frame.setLayout(self.viewer_layout)
        self.viewer_layout.addWidget(self.input_viewer)
        self.viewer_layout.addWidget(self.output_viewer)

        self.right_layout.addWidget(self.viewer_frame)

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
        self.combo_box.addItem('Musical Mode')
        self.combo_box.addItem('Uniform Mode')
        self.combo_box.addItem('Animal Mode')
        self.combo_box.addItem('ECG Abnormalities Mode')
        self.combo_box.currentIndexChanged.connect(self.change_mode)
        self.left_layout.addWidget(self.combo_box)

        layout = QHBoxLayout()
        layout.addWidget(self.left_frame)
        layout.addWidget(self.right_frame)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def change_mode(self, index):
        self.current_mode = self.combo_box.itemText(index)
        self.update_sliders()
        print(self.current_mode)

    def create_sliders(self, slider_num):
        sliders = []
        for i in range(slider_num):
            slider = QSlider(Qt.Orientation.Vertical)
            slider.setMinimum(0)
            slider.setMaximum(100)
            slider.setValue(50)
            sliders.append(slider)
        return sliders

    def update_sliders(self):
        for i in reversed(range(self.slider_layout.count())):
            widget_to_remove = self.slider_layout.itemAt(i).widget()
            self.slider_layout.removeWidget(widget_to_remove)
            widget_to_remove.setParent(None)

        slider_num = 10 if self.current_mode == 'Uniform Mode' else 4
        self.sliders = self.create_sliders(slider_num)
        for i, slider in enumerate(self.sliders):
            self.slider_layout.addWidget(slider)

    def load_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Open WAV File", "", "WAV Files (*.wav);;All Files (*)",
                                                   options=options)
        if file_path:
            self.input_viewer.load_waveform(file_path)
            # self.output_viewer.load_waveform(file_path)

            # ! Example call to plot_output with the same data as input_viewer
            self.plot_output(self.input_viewer.audio_data)
            self.output_viewer.plot_widget.addItem(self.output_viewer.needle)

            self.input_viewer.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
            self.output_viewer.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
            self.update_frequency_graph()

    def plot_output(self, output_data):
        if self.input_viewer.audio_data is not None:
            duration = (len(output_data) / self.input_viewer.sample_rate) / 2
            x = np.linspace(0, duration, len(output_data))
            self.output_viewer.plot_item.setData(x, output_data)
            self.output_viewer.plot_widget.setXRange(x[0], x[-1])

    def update_frequency_graph(self):
        if self.input_viewer.audio_data is not None:
            fft_data = np.fft.fft(self.input_viewer.audio_data)
            fft_freq = np.fft.fftfreq(len(fft_data), 1 / self.input_viewer.sample_rate)

            positive_freqs = fft_freq[:len(fft_freq) // 2]
            positive_magnitudes = np.abs(fft_data[:len(fft_data) // 2])
            self.get_range_of_frequencies(positive_freqs, positive_magnitudes)
            self.freq_plot_item.setData(positive_freqs, positive_magnitudes)

    def update_frequency_graph(self):
        if self.input_viewer.audio_data is not None:
            fft_data = np.fft.fft(self.input_viewer.audio_data)
            fft_freq = np.fft.fftfreq(len(fft_data), 1 / self.input_viewer.sample_rate)

            positive_freqs = fft_freq[:len(fft_freq) // 2]
            positive_magnitudes = np.abs(fft_data[:len(fft_data) // 2])

            self.get_range_of_frequencies(positive_freqs, positive_magnitudes)
            self.freq_plot_item.setData(positive_freqs, positive_magnitudes)

    def get_range_of_frequencies(self, freqs, magnitudes):
        ROF = []
        std_dev = np.std(magnitudes)
        lowest_needed_amp = std_dev / 10

        filtered_freq = [frequency for frequency, amp in zip(freqs, magnitudes) if amp >= lowest_needed_amp]
        filtered_amp = [amp for frequency, amp in zip(freqs, magnitudes) if amp >= lowest_needed_amp]

        diff = np.diff(filtered_freq)
        for i in range(len(diff)):
            if diff[i] - 50 > 0:
                ROF.append(filtered_freq[i])
                ROF.append(filtered_freq[i + 1])

        ROF = ROF[1:-1]
        ROF = list(zip(ROF[::2], ROF[1::2]))
        print("Ranges of Frequencies (ROF):", ROF)

        reconstructed_signal = self.reconstruct_signal_from_filtered(freqs, magnitudes, filtered_freq, filtered_amp)
        self.plot_output(reconstructed_signal)
        return ROF

    def reconstruct_signal_from_filtered(self, original_freqs, original_magnitudes, filtered_freq, filtered_amp):
        n_samples = len(original_freqs) * 2
        fourier_data = np.zeros(n_samples, dtype=complex)

        # Fill Fourier data with filtered frequencies and amplitudes
        for freq, amp in zip(filtered_freq, filtered_amp):
            idx = int(freq * n_samples / self.input_viewer.sample_rate)
            if 0 <= idx < n_samples // 2:
                fourier_data[idx] = amp
                fourier_data[-idx] = amp

        reconstructed_signal = np.fft.ifft(fourier_data).real
        return reconstructed_signal

    def play_audio(self):
        self.input_viewer.play_audio()
        self.output_viewer.play_audio()

    def pause_audio(self):
        self.input_viewer.pause_audio()
        self.output_viewer.pause_audio()

    def rewind_audio(self):
        self.input_viewer.rewind_audio()
        self.output_viewer.rewind_audio()

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
