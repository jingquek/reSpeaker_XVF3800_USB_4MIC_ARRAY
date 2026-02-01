# ReSpeaker XVF3800 Diagnostic Application

A comprehensive diagnostic tool for testing all native features of the reSpeaker XVF3800 device, including audio recording, real-time visualization, and parameter adjustment capabilities.

## Features

### 🔧 Device Control & Monitoring
- **Device Information**: Version, serial number, device ID
- **Connection Status**: Real-time device connection monitoring
- **Parameter Control**: Adjust all audio processing parameters
- **Configuration Management**: Save/clear device configurations

### 🎵 Audio Recording & Analysis
- **Real-time Recording**: Record audio from the reSpeaker XVF3800
- **Live Visualization**: Real-time waveform and frequency spectrum display
- **Audio Histogram**: Analyze audio amplitude distribution
- **Statistics**: Mean, standard deviation, max amplitude analysis
- **Save Recordings**: Export audio to WAV files

### 🎨 LED Control
- **Effect Control**: Off, Breath, Rainbow, Single Color, DoA modes
- **Color Selection**: Custom hex color picker
- **Brightness Control**: 0-255 brightness adjustment
- **Speed Control**: Effect speed adjustment (1-10)

### 🔌 GPIO Control
- **GPI Reading**: Read all General Purpose Input pins
- **GPO Control**: Set General Purpose Output pin states
- **Pin Mapping**: Control specific pins (11, 30, 31, 33, 39)

### 🎯 AEC Monitoring
- **AEC Status**: Check echo cancellation convergence
- **Speech Energy**: Monitor speech energy levels for all beams
- **Azimuth Values**: Track beam direction of arrival
- **Auto-refresh**: Continuous monitoring with configurable intervals

### 📊 Visualization & Analysis
- **Real-time Waveform**: Live audio signal display
- **Frequency Spectrum**: FFT-based frequency analysis
- **Audio Histogram**: Amplitude distribution analysis
- **Parameter Effects**: Visual feedback on setting changes

## Installation

### Prerequisites
- Python 3.7 or higher
- Windows 10/11 (for xvf_host.exe compatibility)
- ReSpeaker XVF3800 device connected via USB

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Required Packages
- `numpy` - Numerical computing
- `matplotlib` - Data visualization
- `pyaudio` - Audio recording and playback
- `tkinter` - GUI framework (usually included with Python)

## Usage

### Starting the Application
```bash
python reSpeaker_XVF3800_Diagnostic_App.py
```

### Basic Workflow
1. **Connect Device**: Ensure your reSpeaker XVF3800 is connected via USB
2. **Check Connection**: Go to "Device Info" tab to verify connection
3. **Adjust Parameters**: Use "Parameter Control" tab to modify audio settings
4. **Test Recording**: Use "Audio Recording" tab to record and analyze audio
5. **Monitor AEC**: Use "AEC Monitoring" tab to check echo cancellation status
6. **Control LEDs**: Use "LED Control" tab to test LED functionality
7. **GPIO Testing**: Use "GPIO Control" tab to test input/output pins

### Audio Recording
1. Go to "Audio Recording" tab
2. Configure sample rate and channels
3. Click "Start Recording" to begin
4. View real-time waveform and spectrum
5. Click "Generate Histogram" to analyze audio distribution
6. Click "Save Recording" to export audio file

### Parameter Adjustment
1. Go to "Parameter Control" tab
2. Adjust sliders for desired parameters:
   - **AUDIO_MGR_MIC_GAIN**: Microphone gain (0-255)
   - **AUDIO_MGR_REF_GAIN**: Reference signal gain (0.0-20.0)
   - **AUDIO_MGR_SYS_DELAY**: System delay (-64 to 256)
   - **PP_AGCGAIN**: AGC gain (0.0-10.0)
   - **PP_AGCMAXGAIN**: Maximum AGC gain (0.0-100.0)
   - **PP_FMIN_SPEINDEX**: Minimum speech index (0.0-5000.0)
   - **AEC_ASROUTGAIN**: ASR output gain (0.0-5.0)
3. Click "Apply All Parameters" to send changes to device
4. Use "Save Configuration" to persist changes

### LED Control
1. Go to "LED Control" tab
2. Select effect mode (Off, Breath, Rainbow, Single Color, DoA)
3. Set color using hex format (e.g., 0xff0000 for red)
4. Adjust brightness (0-255) and speed (1-10)
5. Click "Apply LED Settings"

### AEC Monitoring
1. Go to "AEC Monitoring" tab
2. Click "Check AEC Status" to see convergence status
3. Click "Get Speech Energy" to see energy levels for all beams
4. Click "Get Azimuth Values" to see beam directions
5. Enable "Auto-refresh" for continuous monitoring

## Audio Output Categories

When using audio routing commands, you can select from these categories:

| Category | Description |
|----------|-------------|
| 0 | Silence |
| 1 | Raw microphone data (before amplification) |
| 2 | Unpacked microphone data |
| 3 | Amplified microphone data (with system delay) |
| 4 | Far end reference data |
| 5 | Far end reference data (with system delay) |
| 6 | Processed data (beamformed outputs) |
| 7 | AEC residual / ASR data |
| 8 | User chosen channels |
| 9 | Post SHF DSP channels |
| 10 | Far end at native rate |
| 11 | Amplified microphone data (before system delay) |
| 12 | Amplified far end reference (with system delay) |

## Troubleshooting

### Device Not Found
- Ensure the reSpeaker XVF3800 is connected via USB
- Check that xvf_host.exe is in the correct location
- Verify USB drivers are installed

### Audio Recording Issues
- Check that the device is recognized in Windows audio settings
- Ensure no other applications are using the microphone
- Try different sample rates (8000, 16000, 44100, 48000 Hz)

### Parameter Changes Not Applied
- Verify device connection status
- Check that parameters are within valid ranges
- Use "Save Configuration" to persist changes

### LED Not Responding
- Ensure LED effect is not set to "Off" (0)
- Check that LED power pin (X0D33) is enabled
- Verify color format is correct (hex, e.g., 0xff0000)

## Technical Details

### Based on Official Documentation
This application is based on the [XMOS XVF3800 User Guide](https://www.xmos.com/documentation/XM-014888-PC/html/doc/user_guide/index.html) and implements all native control commands.

### Supported Commands
- All AEC tuning and control commands
- Device metadata commands
- Audio manager commands
- GPIO control commands
- LED control commands

### Audio Processing
- Real-time audio capture using PyAudio
- FFT-based frequency analysis
- Statistical analysis of audio amplitude
- Histogram visualization for parameter effect analysis

## File Structure
```
reSpeaker_XVF3800_USB_4MIC_ARRAY/
├── reSpeaker_XVF3800_Diagnostic_App.py  # Main application
├── requirements.txt                      # Python dependencies
├── README_Diagnostic_App.md             # This documentation
├── XVF3800_Control_Commands_Reference.md # Command reference
├── host_control/
│   └── win32/
│       ├── xvf_host.exe                 # Device control executable
│       └── commands.txt                 # Command script
└── ...
```

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this diagnostic tool.

## License

This project is provided as-is for educational and diagnostic purposes. Please refer to the XMOS documentation for official device specifications and limitations.

