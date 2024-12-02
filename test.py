import wfdb
import matplotlib.pyplot as plt
import csv
record_name = '105'
database = 'mitdb'

print(f"Downloading record {record_name} from {database}...")
wfdb.dl_database(database, dl_dir='./ecg_data', records=[record_name])

record_path = f'./ecg_data/{record_name}'

record = wfdb.rdrecord(record_path)

annotations = wfdb.rdann(record_path, 'atr')

signal = record.p_signal  # ECG signal data
sampling_frequency = record.fs  # Sampling frequency
times = [i / sampling_frequency for i in range(len(signal))]  # Time in seconds
annotation_times = [t / sampling_frequency for t in annotations.sample]  # Annotation times (seconds)
annotation_labels = annotations.symbol  # Annotation labels

plt.figure(figsize=(15, 6))
plt.plot(times, signal[:, 0], label="ECG Signal (Lead 1)", color="blue")
plt.title("ECG Signal with Annotations")
plt.xlabel("Time (s)")
plt.ylabel("Amplitude (mV)")
plt.grid(True)

plt.legend()
plt.show()
print("Annotations:")
for time, label in zip(annotation_times, annotation_labels):
    print(f"Time: {time:.2f} s, Label: {label}")

csv_file_path = './ecg_data/ecg_data.csv'
with open(csv_file_path, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Time (s)', 'Amplitude (mV)', 'Annotation Time (s)', 'Annotation Label'])
    for i in range(len(times)):
        annotation_time = annotation_times[i] if i < len(annotation_times) else ''
        annotation_label = annotation_labels[i] if i < len(annotation_labels) else ''
        writer.writerow([times[i], signal[i, 0], annotation_time, annotation_label])

print(f"Data saved to {csv_file_path}")