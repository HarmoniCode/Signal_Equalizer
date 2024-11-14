import pandas as pd
import numpy as np
from tkinter import Tk, filedialog
from scipy.fft import ifft

def csv_ifft_to_time_domain():
    # Hide Tkinter root window
    Tk().withdraw()

    # Open file dialog to select the input CSV file
    input_file_path = filedialog.askopenfilename(title="Select CSV File", filetypes=[("CSV files", "*.csv")])
    if not input_file_path:
        print("No file selected. Exiting...")
        return

    # Load the CSV data
    data = pd.read_csv(input_file_path, header=None)  # Load without headers

    # Check if the data has at least two columns
    if data.shape[1] < 2:
        print("CSV file must have at least two columns: frequency and amplitude.")
        return

    # Extract the amplitude column for IFFT
    amplitude = data.iloc[:, 1].values  # Assuming the second column is amplitude

    # Perform IFFT on the amplitude data
    time_domain_signal = np.real(ifft(amplitude))

    # Convert to DataFrame for saving
    time_domain_df = pd.DataFrame(time_domain_signal)

    # Open file dialog to save the output CSV file
    output_file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if output_file_path:
        # Save without headers
        time_domain_df.to_csv(output_file_path, index=False, header=False)
        print(f"Time-domain signal saved to {output_file_path}")
    else:
        print("No output file selected. Exiting...")

# Run the function
csv_ifft_to_time_domain()
