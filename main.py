# pip install sounddevice numpy matplotlib

import queue
import threading
import math
import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt

# ========== Config ==========
SAMPLE_RATE = 44100       # Hz
BLOCK_SIZE = 2048         # Frames per audio block
CHANNELS = 1              # Mono
BUFFER_SECONDS = 2.0      # Seconds of audio to display in waveform
PLOT_SAMPLES = int(SAMPLE_RATE * 0.1)  # Show last 0.1s in the waveform

# Calibration controls (applied after FFT frequency calculation)
# - CALIBRATION_SCALE lets you correct sample-rate drift (multiply measured freq).
#   For example, if a 1000 Hz tone shows as 990 Hz, set CALIBRATION_SCALE = 1000/990.
# - CALIBRATION_OFFSET_HZ applies a fixed offset after scaling.
CALIBRATION_SCALE = 1.0
CALIBRATION_OFFSET_HZ = 0.0

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

        # Quadratic (parabolic) interpolation around the peak bin to improve
        # sub-bin accuracy: estimate the vertex of the parabola fitted to the
        # log-magnitude spectrum. Skip if the peak is at an edge bin.
        if 1 <= peak_idx < len(mags) - 1:
            alpha = mags[peak_idx - 1]
            beta = mags[peak_idx]
            gamma = mags[peak_idx + 1]

            denominator = (alpha - 2 * beta + gamma)
            if denominator != 0:
                peak_adj = 0.5 * (alpha - gamma) / denominator
            else:
                peak_adj = 0.0
        else:
            peak_adj = 0.0

        # Convert (potentially sub-bin) index to frequency in Hz
        freq = (peak_idx + peak_adj) * SAMPLE_RATE / len(block)

        # Apply calibration to correct device-specific drift or offsets
        freq = freq * CALIBRATION_SCALE + CALIBRATION_OFFSET_HZ

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


# ============================
# Frequency -> Note mapping
# ============================
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F",
              "F#", "G", "G#", "A", "A#", "B"]


def freq_to_note(freq_hz):
    """
    Convert a frequency in Hz to the nearest musical note name and cents offset.

    Returns:
        note_name (str): e.g. 'A4', 'C#5', or '--' if freq <= 0
        cents (float): how many cents the freq is away from the nearest note
    """
    if freq_hz <= 0:
        return "--", 0.0

    # A4 = MIDI 69 = 440 Hz
    # MIDI number from frequency:
    #   midi = 69 + 12 * log2(f / 440)
    midi_float = 69 + 12 * math.log2(freq_hz / 440.0)
    midi_int = int(round(midi_float))

    # Clamp to a reasonable MIDI range (0–127)
    midi_int = max(0, min(127, midi_int))

    # Note name and octave
    note_index = midi_int % 12
    octave = midi_int // 12 - 1
    note_name = f"{NOTE_NAMES[note_index]}{octave}"

    # Cents difference from the nearest equal-tempered note
    cents = (midi_float - midi_int) * 100.0

    return note_name, cents


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

                note_name, cents = freq_to_note(latest_freq)
                # Example title:
                # Live Waveform - 440.0 Hz - A4 (+0.3 cents)
                ax.set_title(
                    f"Live Waveform - {latest_freq:7.1f} Hz - "
                    f"{note_name} ({cents:+5.1f} cents)"
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
