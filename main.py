from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog, QHBoxLayout
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, QTimer
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
            print('Waveform loaded:' , self.sample_rate)
            print('Audio Signal: ' , self.audio_data)
            duration = (len(self.audio_data) / self.sample_rate)/2
            x = np.linspace(0, duration, len(self.audio_data))
            self.plot_item.setData(x, self.audio_data)
            self.plot_widget.setXRange(x[0], x[-1])
            self.plot_widget.addItem(self.needle)

    def play_audio(self):
        self.media_player.play()
        self.timer.start(35)

    def update_needle(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
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
        was_playing = self.media_player.state() == QMediaPlayer.PlayingState
        self.pause_audio()
        current_position = self.media_player.position()
        self.media_player.setPosition(current_position + 1000)  
        if was_playing:
            self.play_audio()

    def backward_audio(self):
        was_playing = self.media_player.state() == QMediaPlayer.PlayingState
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

        self.viewer_layout = QHBoxLayout()
        
        self.input_viewer = SignalViewer()
        self.output_viewer = SignalViewer()

        self.input_viewer.plot_widget.setXLink(self.output_viewer.plot_widget)
        self.input_viewer.plot_widget.setYLink(self.output_viewer.plot_widget)

        self.viewer_layout.addWidget(self.input_viewer)
        self.viewer_layout.addWidget(self.output_viewer)

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

        layout = QVBoxLayout()
        layout.addLayout(self.viewer_layout)
        layout.addLayout(control_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def load_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Open WAV File", "", "WAV Files (*.wav);;All Files (*)", options=options)
        if file_path:
            self.input_viewer.load_waveform(file_path)
            self.output_viewer.load_waveform(file_path)
            self.input_viewer.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
            self.output_viewer.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))

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