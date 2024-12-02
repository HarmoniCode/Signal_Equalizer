import sys
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QFileDialog, QWidget, QHBoxLayout, QSlider, QFormLayout
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas
)
from matplotlib.figure import Figure
from scipy.fftpack import fft, ifft

class SignalViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Signal Frequency Editor")
        self.setGeometry(100, 100, 1200, 800)

        # Main layout
        main_layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        slider_layout = QFormLayout()  # Organizes sliders and labels

        # Buttons
        self.upload_button = QPushButton("Upload CSV")
        self.upload_button.clicked.connect(self.upload_csv)

        self.apply_button = QPushButton("Apply Changes")
        self.apply_button.clicked.connect(self.apply_changes)

        # Sliders for frequency range adjustment
        self.low_freq_slider = QSlider(Qt.Horizontal)
        self.low_freq_slider.setMinimum(0)
        self.low_freq_slider.setMaximum(100)
        self.low_freq_slider.setValue(20)
        self.low_freq_slider.setToolTip("Low Frequency Limit")

        self.high_freq_slider = QSlider(Qt.Horizontal)
        self.high_freq_slider.setMinimum(0)
        self.high_freq_slider.setMaximum(100)
        self.high_freq_slider.setValue(80)
        self.high_freq_slider.setToolTip("High Frequency Limit")

        self.low_freq_slider.valueChanged.connect(self.update_frequency_range)
        self.high_freq_slider.valueChanged.connect(self.update_frequency_range)

        # Frequency range label
        self.freq_label = QLabel("Frequency Range: 0 Hz - 0 Hz")
        slider_layout.addRow("Low Frequency (Hz)", self.low_freq_slider)
        slider_layout.addRow("High Frequency (Hz)", self.high_freq_slider)
        slider_layout.addRow(self.freq_label)

        button_layout.addWidget(self.upload_button)
        button_layout.addWidget(self.apply_button)

        # Matplotlib canvases for signal viewers
        self.input_canvas = SignalCanvas(title="Input Signal")
        self.freq_canvas = SignalCanvas(title="Frequency Spectrum")
        self.output_canvas = SignalCanvas(title="Output Signal")

        # Add widgets to the main layout
        main_layout.addLayout(button_layout)
        main_layout.addLayout(slider_layout)  # Add the slider layout
        main_layout.addWidget(self.input_canvas)
        main_layout.addWidget(self.freq_canvas)
        main_layout.addWidget(self.output_canvas)

        # Central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Variables to hold signal data
        self.time = None
        self.amplitude = None
        self.output_signal = None
        self.freq = None  # Frequency array for the signal
        self.sampling_rate = None  # Sampling rate for the signal

    def upload_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv)")
        if file_path:
            # Load CSV data
            data = pd.read_csv(file_path)
            self.time = data.iloc[:, 0].values
            self.amplitude = data.iloc[:, 1].values
            self.output_signal = self.amplitude.copy()

            # Calculate the sampling rate
            self.sampling_rate = 1 / (self.time[1] - self.time[0])
            self.freq = np.fft.fftfreq(len(self.amplitude), d=(self.time[1] - self.time[0]))

            # Plot input signal and frequency spectrum
            self.input_canvas.plot(self.time, self.amplitude, "Input Signal")
            self.plot_frequency_spectrum()

    def plot_frequency_spectrum(self):
        # Compute FFT
        fft_values = fft(self.amplitude)
        magnitude = np.abs(fft_values)

        # Plot frequency spectrum
        self.freq_canvas.plot(self.freq[:len(self.freq)//2], magnitude[:len(magnitude)//2], "Frequency Spectrum")

    def apply_changes(self):
        if self.freq is None or self.amplitude is None:
            return  # No data loaded

        # Apply frequency range modifications
        fft_values = fft(self.amplitude)
        low_limit = self.low_freq_slider.value() / 100 * self.sampling_rate / 2
        high_limit = self.high_freq_slider.value() / 100 * self.sampling_rate / 2

        fft_filtered = fft_values.copy()
        for i, f in enumerate(self.freq):
            if not (low_limit <= abs(f) <= high_limit):
                fft_filtered[i] = 0

        # Inverse FFT to get the modified signal
        self.output_signal = np.real(ifft(fft_filtered))

        # Plot the output signal
        self.output_canvas.plot(self.time, self.output_signal, "Output Signal")

    def update_frequency_range(self):
        if self.sampling_rate is None:
            return  # No data loaded

        # Calculate frequency in Hz
        low_limit = self.low_freq_slider.value() / 100 * self.sampling_rate / 2
        high_limit = self.high_freq_slider.value() / 100 * self.sampling_rate / 2

        self.freq_label.setText(f"Frequency Range: {low_limit:.2f} Hz - {high_limit:.2f} Hz")
        self.plot_frequency_spectrum()

class SignalCanvas(FigureCanvas):
    def __init__(self, title=""):
        self.figure = Figure()
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title(title)
        super().__init__(self.figure)

    def plot(self, x, y, title=""):
        self.ax.clear()
        self.ax.plot(x, y, label=title)
        self.ax.set_title(title)
        self.ax.legend()
        self.ax.grid()
        self.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = SignalViewer()
    viewer.show()
    sys.exit(app.exec_())
