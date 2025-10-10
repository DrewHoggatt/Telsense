# process_and_align_final.py
import wave
import numpy as np

# --- Configuration ---
INPUT_FILENAME = 'raw_audio_misaligned.bin'
OUTPUT_FILENAME = 'final_audio_aligned.wav'
AUDIO_FORMAT = {'rate': 32000, 'channels': 1, 'width': 4} # 4 bytes for 32-bit

def process_and_align_file():
    """Reads a misaligned raw binary file, finds the correct alignment,
    corrects the audio data, and saves a clean WAV file."""
    
    print(f"Reading raw data from '{INPUT_FILENAME}'...")
    try:
        with open(INPUT_FILENAME, 'rb') as f:
            raw_bytes = f.read()
    except FileNotFoundError:
        print(f"Error: The file '{INPUT_FILENAME}' was not found.")
        return

    if not raw_bytes:
        print("Error: Raw data file is empty.")
        return

    best_alignment = None
    lowest_energy = float('inf')

    print("Finding optimal alignment by testing all 4 byte offsets...")
    for offset in range(4):
        sliced_bytes = raw_bytes[offset:]
        safe_length = (len(sliced_bytes) // AUDIO_FORMAT['width']) * AUDIO_FORMAT['width']
        trimmed_bytes = sliced_bytes[:safe_length]

        if not trimmed_bytes:
            continue

        # --- THE CRITICAL FIX IS HERE ---
        # The '<' tells NumPy to interpret the bytes as LITTLE-ENDIAN integers.
        raw_samples = np.frombuffer(trimmed_bytes, dtype='<i4')

        # The sign extension logic remains the same and will now work correctly.
        corrected_samples = (raw_samples << 8) >> 8

        energy = np.sum(np.abs(corrected_samples))
        print(f"  - Offset {offset}: Energy = {energy}")

        if energy < lowest_energy:
            lowest_energy = energy
            best_alignment = corrected_samples

    if best_alignment is None:
        print("Error: Could not determine best alignment. Is the input file valid?")
        return

    print(f"Optimal alignment found. Saving corrected audio to '{OUTPUT_FILENAME}'...")
    try:
        with wave.open(OUTPUT_FILENAME, 'wb') as wf:
            wf.setnchannels(AUDIO_FORMAT['channels'])
            wf.setsampwidth(AUDIO_FORMAT['width'])
            wf.setframerate(AUDIO_FORMAT['rate'])
            # The WAV format standard is also little-endian.
            wf.writeframes(best_alignment.astype('<i4').tobytes())
        print("WAV file saved successfully.")
    except Exception as e:
        print(f"Error saving WAV file: {e}")

if __name__ == "__main__":
    process_and_align_file()