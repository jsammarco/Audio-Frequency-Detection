# pip install sounddevice numpy matplotlib

import queue
import threading
import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt

# ========== Config ==========
SAMPLE_RATE = 44100       # Hz
BLOCK_SIZE = 2048         # Frames per audio block
CHANNELS = 1              # Mono
BUFFER_SECONDS = 2.0      # Seconds of audio to display in waveform
PLOT_SAMPLES = int(SAMPLE_RATE * 0.1)  # Show last 0.1s in the waveform

# ============================
# Globals
# ============================
audio_queue = queue.Queue()
latest_freq = 0.0

# A circular buffer to hold audio for plotting
buffer_length = int(SAMPLE_RATE * BUFFER_SECONDS)
audio_buffer = np.zeros(buffer_length, dtype=np.float32)
buffer_index = 0
buffer_lock = threading.Lock()


def audio_callback(indata, frames, time, status):
    """PortAudio callback: receives audio blocks from the mic."""
    if status:
        print(status, flush=True)

    # indata shape: (frames, channels)
    mono_block = indata[:, 0].copy()

    # Send block to queue for processing (FFT, plotting update)
    audio_queue.put(mono_block)


def process_audio_blocks():
    """Thread function: consume audio blocks, update buffer & frequency estimate."""
    global audio_buffer, buffer_index, latest_freq

    while True:
        block = audio_queue.get()
        if block is None:
            break  # Stop signal

        # === Update ring buffer for plotting ===
        with buffer_lock:
            n = len(block)
            end_index = buffer_index + n
            if end_index <= buffer_length:
                audio_buffer[buffer_index:end_index] = block
            else:
                # Wrap around
                first_part = buffer_length - buffer_index
                audio_buffer[buffer_index:] = block[:first_part]
                audio_buffer[:n - first_part] = block[first_part:]
            buffer_index = (buffer_index + n) % buffer_length

        # === Estimate dominant frequency using FFT ===
        # Apply a window to reduce spectral leakage
        window = np.hanning(len(block))
        block_win = block * window

        # Real FFT
        fft_vals = np.fft.rfft(block_win)
        mags = np.abs(fft_vals)

        # Ignore DC (index 0), find peak magnitude bin
        mags[0] = 0
        peak_idx = np.argmax(mags)

        # Convert bin index to frequency in Hz
        freq = peak_idx * SAMPLE_RATE / len(block)

        latest_freq = freq


def get_latest_plot_samples():
    """Return the latest samples from the circular buffer for plotting."""
    with buffer_lock:
        if buffer_index >= PLOT_SAMPLES:
            data = audio_buffer[buffer_index - PLOT_SAMPLES:buffer_index]
        else:
            # Wrap
            first_part = audio_buffer[buffer_length - (PLOT_SAMPLES - buffer_index):]
            second_part = audio_buffer[:buffer_index]
            data = np.concatenate((first_part, second_part))
    return data


def main():
    global latest_freq

    # Start processing thread
    worker_thread = threading.Thread(target=process_audio_blocks, daemon=True)
    worker_thread.start()

    # Set up matplotlib figure
    plt.ion()
    fig, ax = plt.subplots()
    x = np.arange(PLOT_SAMPLES) / SAMPLE_RATE  # time axis in seconds
    line, = ax.plot(x, np.zeros(PLOT_SAMPLES))
    ax.set_ylim(-1.0, 1.0)
    ax.set_xlim(0, x[-1])
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    ax.set_title("Live Waveform - Dominant frequency: -- Hz")
    fig.tight_layout()

    # Open input stream
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        blocksize=BLOCK_SIZE,
        callback=audio_callback,
    )

    print("Starting audio stream. Close the plot window to stop.")
    with stream:
        while plt.fignum_exists(fig.number):
            # Update waveform data
            y = get_latest_plot_samples()
            if len(y) == PLOT_SAMPLES:
                line.set_ydata(y)
                ax.set_title(
                    f"Live Waveform - Dominant frequency: {latest_freq:7.1f} Hz"
                )

            fig.canvas.draw()
            fig.canvas.flush_events()
            plt.pause(0.01)

    # Stop worker thread
    audio_queue.put(None)
    worker_thread.join()
    print("Stopped.")


if __name__ == "__main__":
    main()
