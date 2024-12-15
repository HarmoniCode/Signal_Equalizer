import numpy as np
import soundfile as sf
from PyQt5.QtWidgets import QApplication, QFileDialog


def add_white_noise_with_dialog(noise_level=0.1):
    """
    Add white noise to an audio file selected via a file dialog and save the result to a location of choice.

    Parameters:
    - noise_level (float): The intensity of the noise to be added (default is 0.1).
    """
    # Start a Qt application to open a file dialog
    app = QApplication([])

    # Open a file dialog to choose the input audio file
    input_file, _ = QFileDialog.getOpenFileName(None, "Select Audio File", "", "Audio Files (*.wav *.flac *.aiff)")

    if not input_file:
        print("No input file selected.")
        return

    # Open a file dialog to choose the folder where the noisy audio will be saved
    output_file, _ = QFileDialog.getSaveFileName(None, "Save Noisy Audio", "", "WAV Files (*.wav)")

    if not output_file:
        print("No output file selected.")
        return

    # Check if the selected output file has the correct extension
    if not output_file.endswith(".wav"):
        output_file += ".wav"  # Ensure the file ends with .wav extension

    # Read the input audio file
    audio_data, sample_rate = sf.read(input_file)

    # Normalize the audio data to float32 for processing
    audio_data = audio_data.astype(np.float32)

    # Generate white noise with the same shape as the audio data
    noise = np.random.normal(0, 1, audio_data.shape)

    # Scale the noise by the noise level (you can adjust this to control the intensity)
    noise = noise * noise_level * np.max(np.abs(audio_data))

    # Add the noise to the original audio data
    noisy_audio = audio_data + noise

    # Clip the values to be in the valid range of audio data
    noisy_audio = np.clip(noisy_audio, -1, 1)

    # Save the noisy audio to the selected output file
    sf.write(output_file, noisy_audio, sample_rate)

    print(f"White noise added and saved to {output_file}")


add_white_noise_with_dialog(0.05/2.5)
