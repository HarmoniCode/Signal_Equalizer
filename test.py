import pandas as pd
import numpy as np
from scipy.io import wavfile
import tkinter as tk
from tkinter import filedialog

def convert_wav_to_csv():
    # Open the file dialog to select a WAV file
    root = tk.Tk()
    root.withdraw()  # Hide the Tkinter root window
    file_path = filedialog.askopenfilename(title="Select WAV File", filetypes=[("WAV Files", "*.wav")])

    if file_path:
        sample_rate, data = wavfile.read(file_path)
        duration = len(data) / sample_rate
        time = np.linspace(0., duration, len(data))

        # Create a DataFrame with time and amplitude
        df = pd.DataFrame({'Time': time, 'Amplitude': data})

        # Use file dialog to save the CSV file
        output_file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if output_file:
            df.to_csv(output_file, index=False, header=False)
            print(f"Converted CSV file saved at: {output_file}")
        else:
            print("No output file selected.")

# Run the function
convert_wav_to_csv()