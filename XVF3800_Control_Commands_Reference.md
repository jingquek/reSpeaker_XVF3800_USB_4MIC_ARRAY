# XMOS XVF3800 Control Commands Reference

This document provides a comprehensive reference for all control commands available for the XMOS XVF3800 voice processor, as used in the reSpeaker XVF3800 USB 4MIC Array. All commands are case-sensitive and parameters will be reset to their default values on device reset.

**Source:** [XMOS XVF3800 Control Commands Documentation](https://www.xmos.com/documentation/XM-014888-PC/html/modules/fwk_xvf/doc/user_guide/AA_control_command_appendix.html)

## Table of Contents
- [AEC Tuning and Control Commands](#aec-tuning-and-control-commands)
- [Device Metadata Commands](#device-metadata-commands)
- [Audio Manager Commands](#audio-manager-commands)
- [GPIO Commands](#gpio-commands)
- [Usage Examples](#usage-examples)

---

## AEC Tuning and Control Commands

These commands focus on tuning parameters for the AEC (Acoustic Echo Cancellation) and postprocessing tasks.

### Core AEC Commands

| Command | R/W | Params | Format | Description |
|---------|-----|--------|--------|-------------|
| `SHF_BYPASS` | RW | 1 | uint8 | AEC bypass |
| `AEC_NUM_MICS` | RO | 1 | int32 | Number of microphone inputs into the AEC |
| `AEC_NUM_FARENDS` | RO | 1 | int32 | Number of farend inputs into the AEC |
| `AEC_MIC_ARRAY_TYPE` | RO | 1 | int32 | Microphone array type (1 - linear, 2 - squarecular) |
| `AEC_MIC_ARRAY_GEO` | RO | 12 | float | Microphone array geometry. Each microphone is represented by 3 XYZ coordinates in m |
| `AEC_AZIMUTH_VALUES` | RO | 4 | radians | Azimuth values in radians - beam 1, beam 2, free-running beam, auto-select beam |
| `AEC_SPENERGY_VALUES` | RO | 4 | float | Speech energy level values for each beam. Any value above 0 indicates speech |

### AEC Performance Monitoring

| Command | R/W | Params | Format | Description |
|---------|-----|--------|--------|-------------|
| `AEC_CURRENT_IDLE_TIME` | RO | 1 | uint32 | AEC processing current idle time in 10ns ticks |
| `AEC_MIN_IDLE_TIME` | RO | 1 | uint32 | AEC processing minimum idle time in 10ns ticks |
| `AEC_RESET_MIN_IDLE_TIME` | WO | 1 | uint32 | Reset the AEC minimum idle time |
| `AEC_AECPATHCHANGE` | RO | 1 | int32 | AEC Path Change Detection. Valid range: 0,1 (false,true) |
| `AEC_AECCONVERGED` | RO | 1 | int32 | Flag indicating whether AEC is converged. Valid range: 0,1 (false,true) |

### AEC Filter Control

| Command | R/W | Params | Format | Description |
|---------|-----|--------|--------|-------------|
| `AEC_FILTER_CMD_ABORT` | WO | 1 | int32 | Reset the special command state machine |
| `AEC_HPFONOFF` | RW | 1 | int32 | High-pass Filter on microphone signals. Valid range: 0,1,2,3,4 (0:Off, 1:on70, 2:on125, 3:on150, 4:on180) |
| `AEC_AECSILENCELEVEL` | RW | 2 | float | Power threshold for signal detection in adaptive filter.(set,cur) |
| `AEC_AECEMPHASISONOFF` | RW | 1 | int32 | Pre-emphasis and de-emphasis filtering for AEC. Valid range: 0,1,2 (off,on,on_eq) |

### AEC Gain Control

| Command | R/W | Params | Format | Description |
|---------|-----|--------|--------|-------------|
| `AEC_FAR_EXTGAIN` | RW | 1 | float | External gain in dB applied to the far-end reference signals |
| `AEC_ASROUTGAIN` | RW | 1 | float | ASR output gain (default: 1.0) |

### Beam Control

| Command | R/W | Params | Format | Description |
|---------|-----|--------|--------|-------------|
| `AEC_FIXEDBEAMSAZIMUTH_VALUES` | RW | 2 | radians | Azimuth values in radians for beams in fixed mode - fixed beam 1, fixed beam 2 |
| `AEC_FIXEDBEAMSELEVATION_VALUES` | RW | 2 | radians | Elevation angles in radians for the beams in fixed mode |
| `AEC_FIXEDBEAMSGATING` | RW | 1 | uint8 | Enables/disables gating for beams in fixed mode |

### Path Change Detection

| Command | R/W | Params | Format | Description |
|---------|-----|--------|--------|-------------|
| `AEC_PCD_COUPLINGI` | RW | 1 | float | Sensitivity parameter for PCD. Valid range: [0.0 .. 1.0] |

---

## Device Metadata Commands

Commands for reading device information and version details.

| Command | R/W | Params | Format | Description |
|---------|-----|--------|--------|-------------|
| `VERSION` | RO | 3 | uint8 | Device version information |
| `DEVICE_SERIAL` | RO | 4 | uint8 | Device serial number |
| `DEVICE_ID` | RO | 1 | uint32 | Device identification |

---

## Audio Manager Commands

Commands for controlling audio routing, gain, and processing parameters.

### Audio Routing

| Command | R/W | Params | Format | Description |
|---------|-----|--------|--------|-------------|
| `AUDIO_MGR_OP_L` | RW | 2 | uint8 | Sets category and source for L output channel. Valid range: val0: [0 .. 12] val1: [0 .. 5] |
| `AUDIO_MGR_OP_R` | RW | 2 | uint8 | Sets category and source for R output channel. Valid range: val0: [0 .. 12] val1: [0 .. 5] |
| `AUDIO_MGR_OP_L_PK0` | RW | 2 | uint8 | Sets category and source for first source on L channel in packed mode |
| `AUDIO_MGR_OP_L_PK1` | RW | 2 | uint8 | Sets category and source for second source on L channel in packed mode |
| `AUDIO_MGR_OP_L_PK2` | RW | 2 | uint8 | Sets category and source for third source on L channel in packed mode |
| `AUDIO_MGR_OP_R_PK0` | RW | 2 | uint8 | Sets category and source for first source on R channel in packed mode |
| `AUDIO_MGR_OP_R_PK1` | RW | 2 | uint8 | Sets category and source for second source on R channel in packed mode |
| `AUDIO_MGR_OP_R_PK2` | RW | 2 | uint8 | Sets category and source for third source on R channel in packed mode |
| `AUDIO_MGR_OP_ALL` | RW | 12 | uint8 | Sets category and source for all 3 sources on L and R channels |

### Audio Gain Control

| Command | R/W | Params | Format | Description |
|---------|-----|--------|--------|-------------|
| `AUDIO_MGR_MIC_GAIN` | RW | 1 | uint8 | Microphone gain (default: 90) |
| `AUDIO_MGR_REF_GAIN` | RW | 1 | float | Reference signal gain (default: 8.0) |
| `AUDIO_MGR_SYS_DELAY` | RW | 1 | int32 | Delay applied to reference signal before passing to SHF algorithm. Valid range: [-64 .. 256] |

### Audio Processing

| Command | R/W | Params | Format | Description |
|---------|-----|--------|--------|-------------|
| `AUDIO_MGR_OP_UPSAMPLE` | RW | 2 | uint8 | Sets/gets upsample status for L and R output channels |
| `AUDIO_MGR_FAR_END_DSP_ENABLE` | RW | 1 | uint8 | Enables/disables XVF3800 far-end DSP |
| `I2S_DAC_DSP_ENABLE` | RW | 1 | uint8 | Indicates if the DAC performs DSP on the far-end reference signal |
| `I2S_INACTIVE` | RO | 1 | uint8 | Returns whether the main audio loop is exchanging samples with I2S |

### Post-Processing Parameters

| Command | R/W | Params | Format | Description |
|---------|-----|--------|--------|-------------|
| `PP_FMIN_SPEINDEX` | RW | 1 | float | Post-processing minimum speech index (default: 1300.0) |
| `PP_AGCMAXGAIN` | RW | 1 | float | Post-processing AGC maximum gain (default: 64.0) |
| `PP_AGCGAIN` | RW | 1 | float | Post-processing AGC gain (default: 2.0) |

---

## GPIO Commands

Commands for controlling General Purpose Input/Output pins.

### GPI (General Purpose Input) Commands

| Command | R/W | Params | Format | Description |
|---------|-----|--------|--------|-------------|
| `GPI_INDEX` | RW | 1 | uint8 | Set/get pin index for next and subsequent GPI reads |
| `GPI_EVENT_CONFIG` | RW | 1 | uint8 | Set/get event config for selected pin |
| `GPI_ACTIVE_LEVEL` | RW | 1 | uint8 | Set/get active level for selected pin |
| `GPI_VALUE` | RO | 1 | uint8 | Get current logic level of selected GPI pin |
| `GPI_EVENT_PENDING` | RO | 1 | uint8 | Get whether event was triggered for selected GPI pin |
| `GPI_VALUE_ALL` | RO | 1 | uint32 | Get current logic level of all GPI pins as a bitmap |
| `GPI_EVENT_PENDING_ALL` | RO | 1 | uint32 | Get whether event was triggered for all GPI pins as a bitmap |

### GPO (General Purpose Output) Commands

| Command | R/W | Params | Format | Description |
|---------|-----|--------|--------|-------------|
| `GPO_PORT_PIN_INDEX` | RW | 2 | uint32 | GPO port index and pin index for following commands |
| `GPO_PIN_VAL` | WO | 3 | uint8 | Value to write to one pin of a GPO port |
| `GPO_PIN_ACTIVE_LEVEL` | RW | 1 | uint32 | Active level of the port/pin specified by GPO_PORT_PIN_INDEX |
| `GPO_PIN_PWM_DUTY` | RW | 1 | uint8 | PWM duty cycle of the pin (0-100%) |
| `GPO_PIN_FLASH_MASK` | RW | 1 | uint32 | Serial flash mask for the pin |

---

## Audio Output Categories and Sources

When using audio routing commands (`AUDIO_MGR_OP_L`, `AUDIO_MGR_OP_R`), you need to specify category and source parameters:

### Categories

| Category | Description |
|----------|-------------|
| 0 | Silence |
| 1 | Raw microphone data - before amplification |
| 2 | Unpacked microphone data |
| 3 | Amplified microphone data with system delay |
| 4 | Far end (reference) data |
| 5 | Far end (reference) data with system delay |
| 6 | Processed data (beamformed outputs) |
| 7 | AEC residual / ASR data |
| 8 | User chosen channels |
| 9 | Post SHF DSP channels |
| 10 | Far end at native rate |
| 11 | Amplified microphone data before system delay |
| 12 | Amplified far end (reference) with system delay |

### Sources

| Source | Description |
|--------|-------------|
| 0-3 | Specific microphones/beams accessed by index |
| 0-5 | Various data sources depending on category |

---

## Usage Examples

### Basic Device Information
```bash
# Get device version
xvf_host.exe VERSION

# Get device serial number
xvf_host.exe DEVICE_SERIAL

# Get device ID
xvf_host.exe DEVICE_ID
```

### Audio Gain Control
```bash
# Increase microphone gain
xvf_host.exe AUDIO_MGR_MIC_GAIN 120

# Set reference gain
xvf_host.exe AUDIO_MGR_REF_GAIN 10.0

# Set system delay
xvf_host.exe AUDIO_MGR_SYS_DELAY 12
```

### Audio Routing
```bash
# Set left channel to amplified microphone 0
xvf_host.exe AUDIO_MGR_OP_L 3 0

# Set right channel to far end reference data
xvf_host.exe AUDIO_MGR_OP_R 5 0

# Set left channel to auto-select beam (recommended)
xvf_host.exe AUDIO_MGR_OP_L 6 3
```

### AEC Monitoring
```bash
# Get speech energy values for all beams
xvf_host.exe AEC_SPENERGY_VALUES

# Get azimuth values for all beams
xvf_host.exe AEC_AZIMUTH_VALUES

# Check if AEC is converged
xvf_host.exe AEC_AECCONVERGED
```

### Post-Processing Tuning
```bash
# Set AGC parameters
xvf_host.exe PP_AGCGAIN 3.0
xvf_host.exe PP_AGCMAXGAIN 80.0

# Set minimum speech index
xvf_host.exe PP_FMIN_SPEINDEX 1300.0
```

### GPIO Control
```bash
# Read all GPI values
xvf_host.exe GPI_VALUE_ALL

# Set GPO pin value
xvf_host.exe GPO_PORT_PIN_INDEX 0 30
xvf_host.exe GPO_PIN_VAL 0 30 1
```

---

## Notes

- All commands are case-sensitive
- Parameters will be reset to default values on device reset
- Use `SAVE_CONFIGURATION` to persist changes to flash memory
- Use `CLEAR_CONFIGURATION` to revert to factory defaults
- The reSpeaker XVF3800 supports all XMOS XVF3800 commands except standard GPIO commands (uses custom GPIO system)
- For detailed parameter ranges and default values, refer to the [official XMOS documentation](https://www.xmos.com/documentation/XM-014888-PC/html/modules/fwk_xvf/doc/user_guide/AA_control_command_appendix.html)

---

*This reference is based on XMOS XVF3800 v3.2.1 documentation. Last updated: December 2024*

