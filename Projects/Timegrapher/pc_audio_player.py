# pc_audio_player_final.py
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

# A large, thread-safe queue to act as our primary buffer
audio_queue = queue.Queue(maxsize=400) # Increased size for a larger buffer

# A flag to signal the reader thread to stop
stop_thread = False

def serial_reader_thread():
    """
    Reads data from serial port as fast as possible and puts it into a queue.
    This version is non-blocking and much more efficient.
    """
    global stop_thread
    print("Serial reader thread started.")
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
            print(f"Listening on {SERIAL_PORT}...")
            while not stop_thread:
                # --- KEY IMPROVEMENT: NON-BLOCKING READ ---
                # Check how many bytes are waiting in the serial input buffer
                if ser.in_waiting > 0:
                    # Read all available bytes
                    data_chunk = ser.read(ser.in_waiting)
                    audio_queue.put(data_chunk)
                else:
                    # Briefly sleep if no data is waiting, to prevent a busy-loop
                    time.sleep(0.001)

    except serial.SerialException as e:
        print(f"Error: Could not open port {SERIAL_PORT}. {e}")
    except Exception as e:
        print(f"An error occurred in the serial thread: {e}")
    print("Serial reader thread finished.")


def audio_callback(outdata, frames, time, status):
    """This function is called by sounddevice to get more audio data."""
    if status.output_underflow:
        print('Output underflow!')

    required_bytes = frames * BYTES_PER_SAMPLE
    buffer = b''

    # Pull data from the queue until we have enough for this callback
    while len(buffer) < required_bytes:
        try:
            chunk = audio_queue.get_nowait()
            buffer += chunk
        except queue.Empty:
            # Queue is empty, stop trying to fill the buffer
            print("Warning: Queue empty, outputting some silence.")
            break
            
    # --- THIS IS THE FIX ---
    # Ensure the buffer length is a multiple of the sample size (4 bytes)
    # This trims off any partial samples from the end of the buffer.
    safe_length = (len(buffer) // BYTES_PER_SAMPLE) * BYTES_PER_SAMPLE
    safe_buffer = buffer[:safe_length]
    # ---------------------

    # Convert the now-safe buffer to a NumPy array
    audio_data = np.frombuffer(safe_buffer, dtype=DTYPE)
    
    len_available = len(audio_data)
    len_needed = frames
    
    if len_available >= len_needed:
        # We have enough, provide the requested number of frames
        outdata[:] = audio_data[:len_needed].reshape(-1, 1)
    else:
        # Not enough data, provide what we have and pad the rest with silence
        outdata.fill(0)
        if len_available > 0:
            outdata[:len_available] = audio_data.reshape(-1, 1)

if __name__ == "__main__":
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