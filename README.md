# Audio Frequency Detection

Real-time audio frequency detection, waveform visualization, and musical note identification written in Python.

This project captures live audio from your microphone, displays a continuously updating waveform, estimates the dominant frequency in real time using FFT, **and maps that frequency to the nearest musical note (A4, C#5, etc.)**.

Repository: https://github.com/jsammarco/Audio-Frequency-Detection

---

## Features

- Live microphone audio capture  
- Real-time waveform visualization  
- Dominant tone frequency detection using FFT  
- **Musical note mapping (A4, C#5, etc.) with cents offset**  
- Smooth plot updates via Matplotlib  
- Cross-platform support (Windows, macOS, Linux)

![Screenshot of the live interface capturing 1000hz](https://raw.githubusercontent.com/jsammarco/Audio-Frequency-Detection/d043486c9052d0cde2661c180100faba339c2dfd/screenshot.JPG)
---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/jsammarco/Audio-Frequency-Detection
cd Audio-Frequency-Detection
```

### 2. Install Required Python Packages

```bash
pip install sounddevice numpy matplotlib
```

Make sure your OS microphone permissions allow Python access.

---

## Usage

Run the program:

```bash
python main.py
```

A window will open showing the live waveform.  
The plot title will display:

- Detected frequency (Hz)  
- Nearest musical note (e.g., A4, C#5)  
- Cents difference from the exact note

Example:

```
Live Waveform – 440.1 Hz – A4 (+0.3 cents)
```

Close the window to stop the program.

---

## Calibration

First, verify that the detector is resolving sub-bin peaks correctly. The FFT bin spacing at the default settings is about 21.5 Hz, so very small block-size changes can push readings up or down a bin. The code applies a parabolic (quadratic) interpolation around the strongest bin to recover sub-bin accuracy; this typically removes most “stuck on a bin edge” errors. Once you are getting stable readings, use the calibration constants in `main.py` for any remaining drift:

- `CALIBRATION_SCALE`: Multiplies the measured frequency to correct sample-rate drift.
- `CALIBRATION_OFFSET_HZ`: Adds a fixed offset after scaling.

To solve for both values with two known test tones:

1. Play a reference tone `f1` (e.g., 1000 Hz) and note the measured value `m1` **with calibration left at defaults**.
2. Play a second tone `f2` (e.g., 1100 Hz) and note the measured value `m2`.
3. Compute `CALIBRATION_SCALE = (f2 - f1) / (m2 - m1)`.
4. Compute `CALIBRATION_OFFSET_HZ = f1 - CALIBRATION_SCALE * m1`.

The resulting scale should be close to 1.0 and the offset close to 0. If the values are large, double-check that the peak is stable and that the measured values were taken **before** applying calibration.

---

## How It Works

### Audio Capture
- `sounddevice.InputStream` streams microphone audio in small blocks.
- Audio blocks are added to a thread-safe queue.

### Processing Thread
- Updates a circular buffer for waveform visualization.
- Applies a Hanning window to each audio block.
- Computes real FFT (`rfft`) to determine frequency magnitude.
- Finds the peak bin → converts to Hz.
- Converts frequency to:
  - MIDI note number
  - Note name (A4, C#5, etc.)
  - Cents offset

### Visualization
- Matplotlib updates at ~100 FPS.
- The waveform shows the last 0.1 seconds of audio.
- The window title shows the detected note and frequency.

---

## File Overview

- `main.py` — Main application for reading audio, detecting frequency, mapping notes, and plotting.
- `README.md` — This documentation file.

---

## Musical Note Mapping

The system converts frequency → note using:

```
midi = 69 + 12 * log2(freq / 440)
```

Then determines:
- Note name from MIDI index  
- Octave number  
- Cents deviation:  
  `cents = (midi_float - midi_int) * 100`

---

## Future Enhancements

Planned optional improvements:

- Add a spectrum analyzer panel  
- Noise gating & stability smoothing  
- Large central tuner-style note display  
- Audio recording feature  
- GUI (Tkinter / PyQt) version

---

## License

MIT License. See `LICENSE` file for details.
