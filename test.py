import numpy as np
import csv
from scipy.io.wavfile import write
import tkinter as tk
from tkinter import filedialog


# Function to open a file dialog and select CSV file
def select_csv_file():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.askopenfilename(title="Select CSV File", filetypes=[("CSV Files", "*.csv")])
    return file_path


# Function to save the WAV file with a file dialog
def save_wav_file():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV Files", "*.wav")])
    return file_path


# Function to convert CSV to WAV
def csv_to_wav():
    # Select CSV file
    csv_file = select_csv_file()
    if not csv_file:
        print("No CSV file selected.")
        return

    # Read the CSV into a numpy array (assuming each row is a single sample)
    audio_data = []

    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            audio_data.append(int(row[0]))  # Assuming the audio data is in the first column

    # Convert the list to a numpy array
    audio_data = np.array(audio_data, dtype=np.int16)  # Use np.int16 for 16-bit depth

    # Define the sample rate (samples per second)
    sample_rate = 44100  # Standard sample rate, you can change this if needed

    # Select where to save the WAV file
    wav_file = save_wav_file()
    if not wav_file:
        print("No location selected to save the WAV file.")
        return

    # Write the numpy array as a WAV file
    write(wav_file, sample_rate, audio_data)
    print(f"CSV converted to WAV: {wav_file}")


# Run the conversion
csv_to_wav()