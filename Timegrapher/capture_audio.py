# capture_audio_final.py
import serial
import time
import wave
import sys

# --- Configuration ---
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 2000000
DURATION_SECONDS = 30
AUDIO_FORMAT = {'rate': 32000, 'channels': 1, 'width': 4}
OUTPUT_FILENAME = 'watch_audio.wav'

# --- Framing Protocol Configuration ---
SOF_MARKER = b'\xAA\x55'
PAYLOAD_SIZE = 512

def find_sof_marker(serial_port):
    """Reads byte-by-byte until the SOF marker is found."""
    sync_bytes = bytearray(2)
    # Fill initial window with something that's not the marker
    sync_bytes.extend(b'\x00\x00')
    
    while True:
        new_byte = serial_port.read(1)
        if not new_byte: # Timeout
            return False
            
        # Shift our 2-byte window and check for the marker
        sync_bytes.pop(0)
        sync_bytes.append(new_byte[0])
        
        if sync_bytes == SOF_MARKER:
            return True

def capture_audio():
    """Connects to the Pico, synchronizes to each data frame, and records."""
    audio_data_chunks = []
    
    print(f"Attempting to open serial port {SERIAL_PORT}...")
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
            print("Serial port opened. Capturing...")

            start_time = time.time()
            # --- THE CORRECTED MAIN LOOP ---
            while (time.time() - start_time) < DURATION_SECONDS:
                # 1. Hunt for the marker for every single frame.
                if find_sof_marker(ser):
                    # 2. If the marker is found, read the subsequent payload.
                    chunk = ser.read(PAYLOAD_SIZE)
                    if len(chunk) == PAYLOAD_SIZE:
                        audio_data_chunks.append(chunk)
                    else:
                        print("\nWarning: Incomplete frame received after marker. Data may be corrupt.")
                        # This chunk will be smaller, but we'll keep it for now
                        audio_data_chunks.append(chunk)
                else:
                    # If we time out waiting for a marker, the stream has likely stopped.
                    print("\nError: Timed out waiting for a data frame from the Pico. Stopping capture.")
                    break # Exit the capture loop

                # Progress update
                progress = ((time.time() - start_time) / DURATION_SECONDS) * 100
                sys.stdout.write(f"\rProgress: {progress:.1f}%...")
                sys.stdout.flush()

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        return

    print(f"\nCapture complete. Saving audio to '{OUTPUT_FILENAME}'...")
    final_audio_data = b''.join(audio_data_chunks)
    
    try:
        with wave.open(OUTPUT_FILENAME, 'wb') as wf:
            wf.setnchannels(AUDIO_FORMAT['channels'])
            wf.setsampwidth(AUDIO_FORMAT['width'])
            wf.setframerate(AUDIO_FORMAT['rate'])
            wf.writeframes(final_audio_data)
        print("File saved successfully.")
    except Exception as e:
        print(f"Error saving WAV file: {e}")

if __name__ == "__main__":
    input("Press Enter to start capturing...")
    capture_audio()