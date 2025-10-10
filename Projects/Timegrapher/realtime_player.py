# realtime_player.py
import serial
import sounddevice as sd
import numpy as np
import queue
import threading
import time

# --- Configuration ---
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 2000000
SAMPLE_RATE = 32000
CHANNELS = 1
DTYPE = 'int32'
BYTES_PER_SAMPLE = 4

# A large, thread-safe queue to pass data between threads
audio_queue = queue.Queue(maxsize=400)
stop_thread = False

# A persistent buffer for the audio callback to handle misaligned chunks
callback_buffer = b''

def serial_reader_thread():
    """Reads raw data from the serial port as fast as possible."""
    global stop_thread
    print("Serial reader thread started.")
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
            # --- Initial Flush ---
            # Discard any old data sitting in the buffers to start fresh.
            ser.reset_input_buffer()
            time.sleep(0.1)
            print(f"Listening on {SERIAL_PORT}...")
            
            while not stop_thread:
                if ser.in_waiting > 0:
                    chunk = ser.read(ser.in_waiting)
                    audio_queue.put(chunk)
                else:
                    time.sleep(0.001) # Prevent busy-looping

    except serial.SerialException as e:
        print(f"Error: Could not open port {SERIAL_PORT}. {e}")
    except Exception as e:
        print(f"An error occurred in the serial thread: {e}")
    print("Serial reader thread finished.")


def audio_callback(outdata, frames, time, status):
    """
    The core of the real-time processing.
    Handles alignment, endianness, and sign-extension.
    """
    global callback_buffer
    if status.output_underflow:
        print('Output underflow!')

    # Pull all available data from the queue and append to our persistent buffer
    while not audio_queue.empty():
        callback_buffer += audio_queue.get_nowait()

    # Determine the largest chunk that is a multiple of our sample size
    safe_length = (len(callback_buffer) // BYTES_PER_SAMPLE) * BYTES_PER_SAMPLE
    
    if safe_length == 0:
        # Not enough data for even one full sample, output silence
        outdata.fill(0)
        print("Warning: Starving for data, outputting silence.")
        return

    # Slice the safe portion for processing
    processing_chunk = callback_buffer[:safe_length]
    # Keep the leftover bytes for the next callback
    callback_buffer = callback_buffer[safe_length:]

    # --- Perform the corrections on the aligned data ---
    # 1. Interpret as little-endian 32-bit integers
    raw_samples = np.frombuffer(processing_chunk, dtype='<i4')
    # 2. Perform 24-bit sign extension
    corrected_samples = (raw_samples << 8) >> 8
    
    # --- Output to speaker ---
    len_available = len(corrected_samples)
    len_needed = frames
    
    if len_available >= len_needed:
        outdata[:] = corrected_samples[:len_needed].reshape(-1, 1)
    else:
        outdata.fill(0)
        outdata[:len_available] = corrected_samples.reshape(-1, 1)

if __name__ == "__main__":
    # Ensure the Pico is running the continuous streamer script.
    input("Press Enter to start listening...")

    reader = threading.Thread(target=serial_reader_thread)
    reader.daemon = True
    reader.start()

    print("Priming audio buffer for 0.5 seconds...")
    time.sleep(0.5)
    print(f"Buffer has {audio_queue.qsize()} chunks. Starting audio stream.")

    try:
        with sd.OutputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE, callback=audio_callback):
            print("Audio stream started. Press Enter to stop.")
            input()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Stopping stream...")
        stop_thread = True
        reader.join(timeout=2)