# live_graph_and_player.py
import serial
import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import queue
import threading
from collections import deque

# --- Configuration ---
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 2000000
SAMPLE_RATE = 32000
CHANNELS = 1
DTYPE = 'int32'
BYTES_PER_SAMPLE = 4

# --- NEW: Amplification Factor ---
# Adjust this value to change the playback volume.
# 1.0 = no change, 2.0 = double the volume, 0.5 = half the volume.
AMPLIFICATION_FACTOR = 5


# --- Framing Protocol ---
SOF_MARKER = b'\xAA\x55'
PAYLOAD_SIZE = 512

# --- Plotting Configuration ---
PLOT_WINDOW_SAMPLES = 8000 # 250ms window

# --- Thread-safe Queues ---
serial_data_queue = queue.Queue()
# These two queues will receive the same processed data chunks
plot_chunk_queue = queue.Queue(maxsize=100)
audio_chunk_queue = queue.Queue(maxsize=100)

stop_threads = False

def serial_reader_thread():
    """Reads framed data from serial and puts the raw payload into a queue."""
    global stop_threads
    print("Serial reader thread started.")
    
    def find_sof_marker(ser_port):
        sync_bytes = bytearray(2)
        while not stop_threads:
            new_byte = ser_port.read(1)
            if not new_byte: return False
            sync_bytes.pop(0); sync_bytes.append(new_byte[0])
            if sync_bytes == SOF_MARKER: return True
        return False

    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
            ser.reset_input_buffer()
            print(f"Listening on {SERIAL_PORT}...")
            while not stop_threads:
                if find_sof_marker(ser):
                    chunk = ser.read(PAYLOAD_SIZE)
                    if len(chunk) == PAYLOAD_SIZE:
                        serial_data_queue.put(chunk)
    except Exception as e:
        print(f"Serial thread error: {e}")
    print("Serial reader thread finished.")

def data_processor_distributor_thread():
    """Pulls raw data, processes it, and distributes it to the plot and audio queues."""
    global stop_threads
    print("Data processor thread started.")
    while not stop_threads:
        try:
            raw_chunk = serial_data_queue.get(timeout=1)
            raw_samples = np.frombuffer(raw_chunk, dtype='<i4')
            corrected_samples = (raw_samples << 8) >> 8
            
            # Put the same chunk of processed data into both queues
            if not plot_chunk_queue.full():
                plot_chunk_queue.put(corrected_samples)
            if not audio_chunk_queue.full():
                audio_chunk_queue.put(corrected_samples)

        except queue.Empty:
            continue
    print("Data processor thread finished.")

# --- NEW: A persistent buffer for the audio callback ---
audio_buffer = np.array([], dtype=DTYPE)

def audio_callback(outdata, frames, time, status):
    """
    The function called by the sounddevice stream to get more audio data.
    This version includes an amplification and clipping stage.
    """
    global audio_buffer
    if status:
        print(status)
    
    # Fill our persistent buffer with as much data as is needed
    while len(audio_buffer) < frames:
        try:
            # Pull a new chunk from the queue and append it
            audio_buffer = np.concatenate((audio_buffer, audio_chunk_queue.get_nowait()))
        except queue.Empty:
            # Not enough data; pad with silence and break
            print("Audio buffer underrun!")
            silence_needed = frames - len(audio_buffer)
            samples_to_play = np.concatenate((audio_buffer, np.zeros(silence_needed, dtype=DTYPE)))
            audio_buffer = np.array([], dtype=DTYPE) # Clear buffer
            break # Exit the while loop
    else:
        # This block runs if the while loop completed without a break (i.e., we have enough data)
        samples_to_play = audio_buffer[:frames]
        # Keep the rest of the data for the next call
        audio_buffer = audio_buffer[frames:]

    # --- AMPLIFICATION AND CLIPPING STAGE ---
    # 1. Multiply by the amplification factor. This converts the array to float.
    amplified_samples = samples_to_play * AMPLIFICATION_FACTOR
    
    # 2. Clip the values to the valid 24-bit range to prevent distortion.
    #    The microphone's true range is 24-bit, so we clip to that.
    np.clip(amplified_samples, -2**23, 2**23 - 1, out=amplified_samples)
    
    # 3. Convert back to the required integer type for the sound card.
    final_samples = amplified_samples.astype(DTYPE)
    
    # Assign the final, amplified samples to the output buffer
    outdata[:] = final_samples.reshape(-1, 1)


# --- Matplotlib Plotting Setup ---
fig, ax = plt.subplots()
plot_data = deque([0] * PLOT_WINDOW_SAMPLES, maxlen=PLOT_WINDOW_SAMPLES)
line, = ax.plot(plot_data)
ax.set_ylim(-2**23, 2**23)
ax.set_xlim(0, PLOT_WINDOW_SAMPLES)
ax.set_title("Live Audio Stream")

def update_plot(frame):
    """Updates the graph with new data."""
    global plot_data
    while not plot_chunk_queue.empty():
        samples_chunk = plot_chunk_queue.get_nowait()
        plot_data.extend(samples_chunk) # Append all new samples
    
    line.set_ydata(plot_data)
    return line,

def on_close(event):
    """Handles the plot window being closed."""
    global stop_threads
    print("Plot window closed. Stopping threads...")
    stop_threads = True

if __name__ == "__main__":
    fig.canvas.mpl_connect('close_event', on_close)

    # Start the background threads for reading and processing
    reader = threading.Thread(target=serial_reader_thread, daemon=True)
    processor = threading.Thread(target=data_processor_distributor_thread, daemon=True)
    reader.start()
    processor.start()

    # Give the buffers a moment to prime
    print("Priming buffers for 0.5 seconds...")
    threading.Event().wait(0.5)

    try:
        # Start the audio stream
        stream = sd.OutputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            callback=audio_callback
        )
        stream.start()
        print("Starting animation... Close the plot window to exit.")
        
        # Start the animation
        ani = FuncAnimation(fig, update_plot, interval=50, blit=True)
        plt.show()

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Clean up after the plot window is closed
        if 'stream' in locals() and stream.active:
            stream.stop()
            stream.close()
        stop_threads = True
        reader.join(timeout=2)
        processor.join(timeout=2)
        print("Program finished.")