# Audio Frequency Detection

Real-time audio frequency detection and waveform visualizer written in Python.

This project captures live audio from your microphone, displays a continuously updating waveform, and estimates the dominant frequency in real time using an FFT.  

Repository: https://github.com/jsammarco/Audio-Frequency-Detection

---

## Features

- Live microphone audio capture  
- Real-time waveform visualization  
- Dominant tone frequency detection (FFT-based)  
- Smooth updating plot using Matplotlib  
- Cross‑platform support (Windows, macOS, Linux)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/jsammarco/Audio-Frequency-Detection
cd Audio-Frequency-Detection
```

### 2. Install required Python packages

```bash
pip install sounddevice numpy matplotlib
```

You may also need to allow microphone access in your OS privacy settings.

---

## Usage

Run the program:

```bash
python live_tone_scope.py
```

A live waveform window will appear, updating in real time.  
The detected tone frequency will show in the window title.

Close the window to stop the program.

---

## How It Works

- **sounddevice** streams audio blocks from your microphone  
- A **background thread**:
  - Updates a circular audio buffer for plotting  
  - Computes a windowed FFT for each block  
  - Extracts the strongest frequency component  
- **Matplotlib** continuously updates the waveform plot with the latest data

---

## File Overview

- `live_tone_scope.py` — Main application for audio sampling, plotting, and frequency detection
- `README.md` — Project documentation

---

## Future Enhancements (Optional)

- Add frequency spectrum plot  
- Add smoothing/averaging for frequency stability  
- Display musical note mappings (A4, C#5, etc.)  
- Save detected frequencies to CSV or log file  
- Add GUI interface (Tkinter or PyQt)

---

## License

MIT License. See `LICENSE` file for full details.
