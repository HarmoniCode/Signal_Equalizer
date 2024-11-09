import numpy as np
import soundfile as sf
import sounddevice as sd
import tkinter as tk
from tkinter import filedialog


def upload_and_process_audio():
    # Create a Tkinter window to upload the audio file
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    file_path = filedialog.askopenfilename(title="Select a WAV file", filetypes=[("WAV files", "*.wav")])

    if file_path:
        # Load the audio file
        audio_data, sample_rate = sf.read(file_path)
        print(f"Loaded audio file: {file_path}")
        print(f"Sample rate: {sample_rate} Hz")

        # Apply FFT
        fft_data = np.fft.fft(audio_data)
        fft_freq = np.fft.fftfreq(len(fft_data), 1 / sample_rate)

        # Extract positive frequencies and magnitudes
        positive_freqs = fft_freq[:len(fft_freq) // 2]
        positive_magnitudes = np.abs(fft_data[:len(fft_data) // 2])

        # Plot frequency domain (for visualization)
        print("Positive frequencies:", positive_freqs)
        print("Positive magnitudes:", positive_magnitudes)

        # Apply IFFT (inverse FFT) to reconstruct the signal
        reconstructed_signal = np.fft.ifft(fft_data).real

        # Save the reconstructed audio to a new file
        output_file = 'reconstructed_audio.wav'
        sf.write(output_file, reconstructed_signal, sample_rate)
        print(f"Reconstructed audio saved as: {output_file}")

        # Play the reconstructed audio
        sd.play(reconstructed_signal, sample_rate)
        print("Playing reconstructed audio...")
        sd.wait()  # Wait until audio has finished playing


# Run the function to upload and process the audio file
upload_and_process_audio()
