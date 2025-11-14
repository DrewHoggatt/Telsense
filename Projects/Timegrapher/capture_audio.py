
# capture_continuous.py
import serial
import time
import sys

# --- Configuration ---
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 2000000
DURATION_SECONDS = 30
OUTPUT_FILENAME = 'raw_audio_misaligned.bin'

def capture_raw_audio():
    """Opens the serial port and saves all incoming data for a set duration."""
    print(f"Attempting to open serial port {SERIAL_PORT}...")
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser, open(OUTPUT_FILENAME, 'wb') as f:
            print(f"Serial port opened. Capturing {DURATION_SECONDS} seconds of raw data...")
            start_time = time.time()
            last_update_time = start_time

            while (time.time() - start_time) < DURATION_SECONDS:
                if ser.in_waiting > 0:
                    chunk = ser.read(ser.in_waiting)
                    f.write(chunk)
                
                # Progress update
                if (time.time() - last_update_time) > 1.0:
                    progress = ((time.time() - start_time) / DURATION_SECONDS) * 100
                    sys.stdout.write(f"\rProgress: {progress:.1f}%...")
                    sys.stdout.flush()
                    last_update_time = time.time()

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        return

    print(f"\nRaw data capture complete. Misaligned data saved to '{OUTPUT_FILENAME}'.")

if __name__ == "__main__":
    input("Press Enter to start capturing...")
    capture_raw_audio()