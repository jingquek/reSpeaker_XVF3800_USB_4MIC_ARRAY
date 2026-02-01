#!/usr/bin/env python3
"""
ReSpeaker XVF3800 Diagnostic Application
========================================

A comprehensive diagnostic tool for testing all native features of the reSpeaker XVF3800 device.
Includes audio recording, real-time visualization, and parameter adjustment capabilities.

Based on XMOS XVF3800 User Guide: https://www.xmos.com/documentation/XM-014888-PC/html/doc/user_guide/index.html

Features:
- Device information and status monitoring
- Audio recording with real-time visualization
- Parameter adjustment and testing
- Audio histogram analysis
- LED control testing
- GPIO control testing
- AEC monitoring and tuning
- Beamforming analysis
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import threading
import time
import json
import os
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pyaudio
import wave
import queue
from collections import deque
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class XVF3800DiagnosticApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ReSpeaker XVF3800 Diagnostic Application")
        self.root.geometry("1400x900")
        
        # Device control
        self.xvf_host_path = self.find_xvf_host()
        self.device_connected = False
        self.device_info = {}
        
        # Audio listening and recording
        self.audio_listening = False
        self.audio_recording = False
        self.audio_playing = False
        self.audio_paused = False
        self.audio_stream = None
        self.audio_data_queue = queue.Queue()
        self.audio_buffer = deque(maxlen=10000)  # Store more audio samples for better visualization
        self.recording_start_time = None
        self.recording_duration_timer = None
        self.recording_paused_time = 0
        
        # Time-based pattern visualization
        self.time_pattern_buffer = deque(maxlen=50000)  # Store more data for time pattern
        self.pattern_start_time = None
        self.sample_rate = 16000  # Default sample rate for time calculations
        
        # Audio device management
        self.device_list = []
        self.selected_device_index = None
        
        # Audio playback
        self.audio_playing = False
        self.playback_paused = False
        self.playback_stream = None
        self.loaded_audio_data = None
        self.loaded_audio_file = None
        self.playback_position = 0
        self.playback_timer = None
        
        # Audio devices
        self.audio_devices = {}
        self.selected_device_index = None
        
        # Visualization
        self.fig = Figure(figsize=(12, 8), dpi=100)
        self.setup_plots()
        
        # Current parameters
        self.current_params = {
            'AUDIO_MGR_MIC_GAIN': 90,
            'AUDIO_MGR_REF_GAIN': 8.0,
            'AUDIO_MGR_SYS_DELAY': -32,
            'PP_AGCGAIN': 2.0,
            'PP_AGCMAXGAIN': 64.0,
            'PP_FMIN_SPEINDEX': 1300.0,
            'AEC_ASROUTGAIN': 1.0,
            'LED_EFFECT': 0,
            'LED_COLOR': 0x000000,
            'LED_BRIGHTNESS': 255,
            'LED_SPEED': 1
        }
        
        self.setup_ui()
        self.check_device_connection()
        
    def find_xvf_host(self):
        """Find the xvf_host.exe executable"""
        possible_paths = [
            Path(__file__).parent / "host_control" / "win32" / "xvf_host.exe",
            Path(__file__).parent / "host_control" / "win32" / "reSpeakerXVF" / "xvf_host.exe",
            Path("host_control/win32/xvf_host.exe"),
            Path("host_control/win32/reSpeakerXVF/xvf_host.exe")
        ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"Found xvf_host.exe at: {path}")
                return str(path)
        
        logger.error("xvf_host.exe not found!")
        return None
    
    def setup_ui(self):
        """Setup the user interface"""
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_device_info_tab()
        self.create_audio_recording_tab()
        self.create_parameter_control_tab()
        self.create_led_control_tab()
        self.create_gpio_control_tab()
        self.create_aec_monitoring_tab()
        self.create_visualization_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_device_info_tab(self):
        """Create device information tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Device Info")
        
        # Device status frame
        status_frame = ttk.LabelFrame(tab, text="Device Status", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.device_status_var = tk.StringVar()
        self.device_status_var.set("Checking connection...")
        ttk.Label(status_frame, textvariable=self.device_status_var).pack()
        
        # Refresh button
        ttk.Button(status_frame, text="Refresh", command=self.check_device_connection).pack(pady=5)
        
        # Device information frame
        info_frame = ttk.LabelFrame(tab, text="Device Information", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.info_text = tk.Text(info_frame, height=20, width=80)
        scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=scrollbar.set)
        
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_audio_recording_tab(self):
        """Create audio recording tab with simplified controls"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Audio Recording")
        
        # Main control section
        main_frame = ttk.LabelFrame(tab, text="Audio Controls", padding=15)
        main_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Three main buttons in a row
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # LISTEN button - activates mic and waveforms
        self.listen_button = ttk.Button(button_frame, text="👂 LISTEN", 
                                       command=self.toggle_listening, width=15)
        self.listen_button.pack(side=tk.LEFT, padx=10, expand=True)
        
        # RECORD button - records audio
        self.record_button = ttk.Button(button_frame, text="● RECORD", 
                                       command=self.toggle_recording, state=tk.DISABLED, width=15)
        self.record_button.pack(side=tk.LEFT, padx=10, expand=True)
        
        # PLAYBACK button - plays last recorded audio through speakers
        self.playback_button = ttk.Button(button_frame, text="▶ PLAYBACK", 
                                         command=self.toggle_playback, state=tk.DISABLED, width=15)
        self.playback_button.pack(side=tk.LEFT, padx=10, expand=True)
        
        # Status display
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=10)
        
        self.audio_status_var = tk.StringVar()
        self.audio_status_var.set("Ready - Click LISTEN to start")
        status_label = ttk.Label(status_frame, textvariable=self.audio_status_var, 
                                font=('Arial', 12, 'bold'))
        status_label.pack()
        
        # Recording duration (only shown when recording)
        self.recording_duration_var = tk.StringVar()
        self.recording_duration_var.set("")
        self.duration_label = ttk.Label(status_frame, textvariable=self.recording_duration_var, 
                                       font=('Arial', 14, 'bold'), foreground='red')
        # Don't pack initially - will pack when recording starts
        
        # Audio device selection
        device_frame = ttk.LabelFrame(tab, text="Audio Device", padding=10)
        device_frame.pack(fill=tk.X, padx=10, pady=5)
        
        device_select_frame = ttk.Frame(device_frame)
        device_select_frame.pack(fill=tk.X)
        
        ttk.Label(device_select_frame, text="Device:").pack(side=tk.LEFT)
        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(device_select_frame, textvariable=self.device_var, 
                                        state="readonly", width=50)
        self.device_combo.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        ttk.Button(device_select_frame, text="Refresh", 
                  command=self.refresh_audio_devices).pack(side=tk.RIGHT, padx=5)
        
        # Audio settings (hidden but needed for functions)
        self.sample_rate_var = tk.StringVar(value="16000")
        self.channels_var = tk.StringVar(value="2")
        
        # Initialize audio devices
        self.refresh_audio_devices()
        self.device_combo.bind('<<ComboboxSelected>>', self.on_device_selected)
        
        # Waveform display
        viz_frame = ttk.LabelFrame(tab, text="Live Audio Visualization", padding=10)
        viz_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create waveform figure with time-based pattern view
        self.waveform_fig = Figure(figsize=(14, 8), dpi=100)
        self.waveform_ax1 = self.waveform_fig.add_subplot(311)  # Real-time waveform
        self.waveform_ax2 = self.waveform_fig.add_subplot(312)  # Time pattern (zoomed out)
        self.waveform_ax3 = self.waveform_fig.add_subplot(313)  # Amplitude envelope over time
        
        self.waveform_fig.tight_layout()
        
        self.audio_canvas = FigureCanvasTkAgg(self.waveform_fig, viz_frame)
        self.audio_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def create_parameter_control_tab(self):
        """Create parameter control tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Parameter Control")
        
        # Create scrollable frame
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Audio Manager Parameters
        audio_frame = ttk.LabelFrame(scrollable_frame, text="Audio Manager Parameters", padding=10)
        audio_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.create_parameter_controls(audio_frame, {
            'AUDIO_MGR_MIC_GAIN': {'type': 'int', 'range': (0, 255), 'default': 90},
            'AUDIO_MGR_REF_GAIN': {'type': 'float', 'range': (0.0, 20.0), 'default': 8.0},
            'AUDIO_MGR_SYS_DELAY': {'type': 'int', 'range': (-64, 256), 'default': -32}
        })
        
        # Post-Processing Parameters
        pp_frame = ttk.LabelFrame(scrollable_frame, text="Post-Processing Parameters", padding=10)
        pp_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.create_parameter_controls(pp_frame, {
            'PP_AGCGAIN': {'type': 'float', 'range': (0.0, 10.0), 'default': 2.0},
            'PP_AGCMAXGAIN': {'type': 'float', 'range': (0.0, 100.0), 'default': 64.0},
            'PP_FMIN_SPEINDEX': {'type': 'float', 'range': (0.0, 5000.0), 'default': 1300.0},
            'AEC_ASROUTGAIN': {'type': 'float', 'range': (0.0, 5.0), 'default': 1.0}
        })
        
        # Control buttons
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Apply All Parameters", 
                  command=self.apply_all_parameters).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset to Defaults", 
                  command=self.reset_parameters).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save Configuration", 
                  command=self.save_configuration).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Configuration", 
                  command=self.clear_configuration).pack(side=tk.LEFT, padx=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_led_control_tab(self):
        """Create LED control tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="LED Control")
        
        # LED Effect Control
        effect_frame = ttk.LabelFrame(tab, text="LED Effect Control", padding=10)
        effect_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(effect_frame, text="Effect:").grid(row=0, column=0, sticky=tk.W)
        self.led_effect_var = tk.StringVar(value="0")
        effect_combo = ttk.Combobox(effect_frame, textvariable=self.led_effect_var,
                                   values=["0", "1", "2", "3", "4"],
                                   state="readonly")
        effect_combo.grid(row=0, column=1, padx=5)
        effect_combo['values'] = ["0 - Off", "1 - Breath", "2 - Rainbow", "3 - Single Color", "4 - DoA"]
        
        ttk.Button(effect_frame, text="Set Effect", 
                  command=self.set_led_effect).grid(row=0, column=2, padx=10)
        
        # LED Color Control
        color_frame = ttk.LabelFrame(tab, text="LED Color Control", padding=10)
        color_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(color_frame, text="Color (Hex):").grid(row=0, column=0, sticky=tk.W)
        self.led_color_var = tk.StringVar(value="0xff0000")
        ttk.Entry(color_frame, textvariable=self.led_color_var, width=10).grid(row=0, column=1, padx=5)
        
        ttk.Button(color_frame, text="Set Color", 
                  command=self.set_led_color).grid(row=0, column=2, padx=10)
        
        # LED Brightness and Speed
        brightness_frame = ttk.LabelFrame(tab, text="LED Brightness & Speed", padding=10)
        brightness_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(brightness_frame, text="Brightness:").grid(row=0, column=0, sticky=tk.W)
        self.led_brightness_var = tk.StringVar(value="255")
        brightness_scale = ttk.Scale(brightness_frame, from_=0, to=255, 
                                   variable=self.led_brightness_var, orient=tk.HORIZONTAL)
        brightness_scale.grid(row=0, column=1, padx=5, sticky=tk.W+tk.E)
        
        ttk.Label(brightness_frame, text="Speed:").grid(row=1, column=0, sticky=tk.W)
        self.led_speed_var = tk.StringVar(value="1")
        speed_scale = ttk.Scale(brightness_frame, from_=1, to=10, 
                              variable=self.led_speed_var, orient=tk.HORIZONTAL)
        speed_scale.grid(row=1, column=1, padx=5, sticky=tk.W+tk.E)
        
        ttk.Button(brightness_frame, text="Apply LED Settings", 
                  command=self.apply_led_settings).grid(row=2, column=0, columnspan=2, pady=10)
    
    def create_gpio_control_tab(self):
        """Create GPIO control tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="GPIO Control")
        
        # GPI Reading
        gpi_frame = ttk.LabelFrame(tab, text="GPI (Input) Reading", padding=10)
        gpi_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(gpi_frame, text="Read GPI Values", 
                  command=self.read_gpi_values).pack(side=tk.LEFT, padx=5)
        
        self.gpi_values_var = tk.StringVar()
        ttk.Label(gpi_frame, textvariable=self.gpi_values_var).pack(side=tk.LEFT, padx=20)
        
        # GPO Control
        gpo_frame = ttk.LabelFrame(tab, text="GPO (Output) Control", padding=10)
        gpo_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(gpo_frame, text="Pin:").grid(row=0, column=0, sticky=tk.W)
        self.gpo_pin_var = tk.StringVar(value="30")
        ttk.Combobox(gpo_frame, textvariable=self.gpo_pin_var,
                    values=["11", "30", "31", "33", "39"]).grid(row=0, column=1, padx=5)
        
        ttk.Label(gpo_frame, text="Value:").grid(row=0, column=2, sticky=tk.W, padx=(20,0))
        self.gpo_value_var = tk.StringVar(value="0")
        ttk.Combobox(gpo_frame, textvariable=self.gpo_value_var,
                    values=["0", "1"]).grid(row=0, column=3, padx=5)
        
        ttk.Button(gpo_frame, text="Set GPO", 
                  command=self.set_gpo_value).grid(row=0, column=4, padx=10)
        
        ttk.Button(gpo_frame, text="Read GPO Values", 
                  command=self.read_gpo_values).grid(row=1, column=0, pady=10)
        
        self.gpo_values_var = tk.StringVar()
        ttk.Label(gpo_frame, textvariable=self.gpo_values_var).grid(row=1, column=1, columnspan=3, sticky=tk.W, padx=5)
    
    def create_aec_monitoring_tab(self):
        """Create AEC monitoring tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="AEC Monitoring")
        
        # AEC Status
        status_frame = ttk.LabelFrame(tab, text="AEC Status", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(status_frame, text="Check AEC Status", 
                  command=self.check_aec_status).pack(side=tk.LEFT, padx=5)
        
        self.aec_status_var = tk.StringVar()
        ttk.Label(status_frame, textvariable=self.aec_status_var).pack(side=tk.LEFT, padx=20)
        
        # Speech Energy Monitoring
        energy_frame = ttk.LabelFrame(tab, text="Speech Energy Monitoring", padding=10)
        energy_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(energy_frame, text="Get Speech Energy", 
                  command=self.get_speech_energy).pack(side=tk.LEFT, padx=5)
        
        self.speech_energy_var = tk.StringVar()
        ttk.Label(energy_frame, textvariable=self.speech_energy_var).pack(side=tk.LEFT, padx=20)
        
        # Azimuth Values
        azimuth_frame = ttk.LabelFrame(tab, text="Beam Azimuth Values", padding=10)
        azimuth_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(azimuth_frame, text="Get Azimuth Values", 
                  command=self.get_azimuth_values).pack(side=tk.LEFT, padx=5)
        
        self.azimuth_values_var = tk.StringVar()
        ttk.Label(azimuth_frame, textvariable=self.azimuth_values_var).pack(side=tk.LEFT, padx=20)
        
        # Auto-refresh
        self.auto_refresh_var = tk.BooleanVar()
        ttk.Checkbutton(tab, text="Auto-refresh AEC data", 
                       variable=self.auto_refresh_var,
                       command=self.toggle_auto_refresh).pack(pady=10)
        
        # Real-time AEC Visualization
        viz_frame = ttk.LabelFrame(tab, text="Real-time AEC Visualization", padding=10)
        viz_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create AEC visualization figure
        self.aec_fig = Figure(figsize=(12, 6), dpi=100)
        self.aec_ax1 = self.aec_fig.add_subplot(221)  # Speech Energy
        self.aec_ax2 = self.aec_fig.add_subplot(222)  # Azimuth Values
        self.aec_ax3 = self.aec_fig.add_subplot(223)  # AEC Status
        self.aec_ax4 = self.aec_fig.add_subplot(224)  # Energy Histogram
        
        self.aec_fig.tight_layout()
        
        self.aec_canvas = FigureCanvasTkAgg(self.aec_fig, viz_frame)
        self.aec_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Initialize AEC data storage
        self.aec_energy_history = deque(maxlen=100)
        self.aec_azimuth_history = deque(maxlen=100)
        self.aec_convergence_history = deque(maxlen=100)
    
    def create_visualization_tab(self):
        """Create visualization tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Audio Analysis")
        
        # Histogram controls
        controls_frame = ttk.LabelFrame(tab, text="Histogram Controls", padding=10)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(controls_frame, text="Generate Histogram", 
                  command=self.generate_histogram).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Clear Data", 
                  command=self.clear_audio_data).pack(side=tk.LEFT, padx=5)
        
        # Histogram display
        hist_frame = ttk.LabelFrame(tab, text="Audio Histogram", padding=10)
        hist_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.hist_canvas = FigureCanvasTkAgg(self.fig, hist_frame)
        self.hist_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def setup_plots(self):
        """Setup matplotlib plots"""
        self.ax1 = self.fig.add_subplot(221)  # Real-time audio waveform
        self.ax2 = self.fig.add_subplot(222)  # Audio histogram
        self.ax3 = self.fig.add_subplot(223)  # Frequency spectrum
        self.ax4 = self.fig.add_subplot(224)  # Parameter effects
        
        self.fig.tight_layout()
    
    def create_parameter_controls(self, parent, parameters):
        """Create parameter control widgets"""
        row = 0
        for param_name, param_info in parameters.items():
            ttk.Label(parent, text=f"{param_name}:").grid(row=row, column=0, sticky=tk.W, pady=2)
            
            if param_info['type'] == 'int':
                var = tk.IntVar(value=param_info['default'])
                scale = ttk.Scale(parent, from_=param_info['range'][0], 
                                to=param_info['range'][1], variable=var, orient=tk.HORIZONTAL)
                scale.grid(row=row, column=1, padx=5, sticky=tk.W+tk.E)
                
                value_label = ttk.Label(parent, text=str(param_info['default']))
                value_label.grid(row=row, column=2, padx=5)
                
                # Update label when scale changes
                def update_label(val, label=value_label):
                    label.config(text=str(int(float(val))))
                scale.configure(command=update_label)
                
            elif param_info['type'] == 'float':
                var = tk.DoubleVar(value=param_info['default'])
                scale = ttk.Scale(parent, from_=param_info['range'][0], 
                                to=param_info['range'][1], variable=var, orient=tk.HORIZONTAL)
                scale.grid(row=row, column=1, padx=5, sticky=tk.W+tk.E)
                
                value_label = ttk.Label(parent, text=f"{param_info['default']:.2f}")
                value_label.grid(row=row, column=2, padx=5)
                
                # Update label when scale changes
                def update_label(val, label=value_label):
                    label.config(text=f"{float(val):.2f}")
                scale.configure(command=update_label)
            
            # Store reference to variable
            setattr(self, f"{param_name.lower()}_var", var)
            row += 1
    
    def run_xvf_command(self, command, *args):
        """Run xvf_host command"""
        if not self.xvf_host_path:
            logger.error("xvf_host.exe not found!")
            return None
        
        cmd = [self.xvf_host_path] + [command] + [str(arg) for arg in args]
        logger.info(f"Running command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.error(f"Command failed: {result.stderr}")
                return None
        except subprocess.TimeoutExpired:
            logger.error("Command timed out")
            return None
        except Exception as e:
            logger.error(f"Error running command: {e}")
            return None
    
    def check_device_connection(self):
        """Check if device is connected and get basic info"""
        def check_connection():
            self.status_var.set("Checking device connection...")
            
            # Get version
            version = self.run_xvf_command("VERSION")
            if version:
                self.device_connected = True
                self.device_status_var.set("Device Connected")
                self.device_info['version'] = version
                
                # Get additional device info
                serial = self.run_xvf_command("DEVICE_SERIAL")
                if serial:
                    self.device_info['serial'] = serial
                
                device_id = self.run_xvf_command("DEVICE_ID")
                if device_id:
                    self.device_info['device_id'] = device_id
                
                # Update info display
                info_text = f"Device Version: {version}\n"
                if 'serial' in self.device_info:
                    info_text += f"Serial Number: {serial}\n"
                if 'device_id' in self.device_info:
                    info_text += f"Device ID: {device_id}\n"
                
                self.info_text.delete(1.0, tk.END)
                self.info_text.insert(1.0, info_text)
                
                self.status_var.set("Device connected successfully")
            else:
                self.device_connected = False
                self.device_status_var.set("Device Not Connected")
                self.status_var.set("Device not found")
        
        threading.Thread(target=check_connection, daemon=True).start()
    
    def toggle_recording(self):
        """Toggle audio recording"""
        if not self.audio_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def refresh_audio_devices(self):
        """Refresh the list of available audio devices"""
        try:
            audio = pyaudio.PyAudio()
            self.audio_devices = {}
            device_list = []
            
            for i in range(audio.get_device_count()):
                device_info = audio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:  # Input devices only
                    device_name = device_info['name']
                    device_key = f"{device_name} (Channels: {device_info['maxInputChannels']}, Rate: {device_info['defaultSampleRate']})"
                    self.audio_devices[device_key] = i
                    device_list.append(device_key)
            
            audio.terminate()
            
            # Update combobox
            self.audio_device_combo['values'] = device_list
            
            # Auto-select reSpeaker device if available
            for device_key in device_list:
                if "respeaker" in device_key.lower() or "xvf3800" in device_key.lower():
                    self.audio_device_var.set(device_key)
                    self.selected_device_index = self.audio_devices[device_key]
                    break
            else:
                # Select first device if no reSpeaker found
                if device_list:
                    self.audio_device_var.set(device_list[0])
                    self.selected_device_index = self.audio_devices[device_list[0]]
            
            # Bind selection change
            self.audio_device_combo.bind('<<ComboboxSelected>>', self.on_device_selected)
            
        except Exception as e:
            logger.error(f"Error refreshing audio devices: {e}")
    
    def on_device_selected(self, event=None):
        """Handle audio device selection"""
        selected_device = self.audio_device_var.get()
        if selected_device in self.audio_devices:
            self.selected_device_index = self.audio_devices[selected_device]
            logger.info(f"Selected audio device: {selected_device}")
    
    def toggle_listening(self):
        """Toggle audio listening (for visualization only)"""
        if self.audio_listening:
            self.stop_listening()
        else:
            self.start_listening()
    
    def toggle_playback(self):
        """Toggle audio playback"""
        if self.audio_playing:
            self.stop_playback()
        else:
            self.start_playback()
    
    def start_listening(self):
        """Start audio listening for visualization"""
        try:
            self.audio = pyaudio.PyAudio()
            
            # Use selected device
            if self.selected_device_index is None:
                messagebox.showerror("Error", "No audio device selected!")
                return
            
            device_index = self.selected_device_index
            device_info = self.audio.get_device_info_by_index(device_index)
            device_name = device_info['name']
            
            sample_rate = int(self.sample_rate_var.get())
            channels = int(self.channels_var.get())
            
            # Test if the device supports the requested parameters
            try:
                test_stream = self.audio.open(
                    format=pyaudio.paInt16,
                    channels=channels,
                    rate=sample_rate,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=1024
                )
                test_stream.close()
            except Exception as e:
                logger.warning(f"Device doesn't support requested parameters, trying device defaults: {e}")
                # Try with device's default parameters
                sample_rate = int(device_info['defaultSampleRate'])
                channels = min(device_info['maxInputChannels'], 2)  # Limit to 2 channels max
                self.sample_rate_var.set(str(sample_rate))
                self.channels_var.set(str(channels))
                
                # Test again with device defaults
                try:
                    test_stream = self.audio.open(
                        format=pyaudio.paInt16,
                        channels=channels,
                        rate=sample_rate,
                        input=True,
                        input_device_index=device_index,
                        frames_per_buffer=1024
                    )
                    test_stream.close()
                except Exception as e2:
                    logger.warning(f"Device defaults failed, trying fallback: {e2}")
                    # Final fallback - try common parameters
                    for fallback_rate in [44100, 48000, 16000, 8000]:
                        try:
                            test_stream = self.audio.open(
                                format=pyaudio.paInt16,
                                channels=1,  # Mono as fallback
                                rate=fallback_rate,
                                input=True,
                                input_device_index=device_index,
                                frames_per_buffer=1024
                            )
                            test_stream.close()
                            sample_rate = fallback_rate
                            channels = 1
                            self.sample_rate_var.set(str(sample_rate))
                            self.channels_var.set(str(channels))
                            break
                        except:
                            continue
            
            self.audio_stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=sample_rate,
                input=True,
                input_device_index=device_index,
                stream_callback=self.audio_callback,
                frames_per_buffer=1024
            )
            
            self.audio_stream.start_stream()
            self.audio_listening = True
            self.listen_button.config(text="Stop Listening")
            self.record_button.config(state=tk.NORMAL)
            self.audio_status_var.set(f"Listening from: {device_name}")
            self.status_var.set("Audio listening started")
            
            # Start visualization update
            self.update_visualization()
            
        except Exception as e:
            logger.error(f"Error starting listening: {e}")
            messagebox.showerror("Error", f"Failed to start listening: {e}\n\nTry checking your audio device settings.")
    
    def stop_listening(self):
        """Stop audio listening"""
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None
        
        if hasattr(self, 'audio'):
            self.audio.terminate()
        
        self.audio_listening = False
        self.listen_button.config(text="👂 LISTEN")
        self.record_button.config(state=tk.DISABLED)
        self.audio_status_var.set("Ready - Click LISTEN to start")
        self.status_var.set("Audio listening stopped")
        
        # Reset pattern visualization
        self.time_pattern_buffer.clear()
        self.pattern_start_time = None
    
    def start_recording(self):
        """Start audio recording"""
        try:
            self.audio = pyaudio.PyAudio()
            
            # Use selected device
            if self.selected_device_index is None:
                messagebox.showerror("Error", "No audio device selected!")
                return
            
            device_index = self.selected_device_index
            device_info = self.audio.get_device_info_by_index(device_index)
            device_name = device_info['name']
            
            sample_rate = int(self.sample_rate_var.get())
            channels = int(self.channels_var.get())
            
            # Test if the device supports the requested parameters
            try:
                test_stream = self.audio.open(
                    format=pyaudio.paInt16,
                    channels=channels,
                    rate=sample_rate,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=1024
                )
                test_stream.close()
            except Exception as e:
                logger.warning(f"Device doesn't support requested parameters, trying device defaults: {e}")
                # Try with device's default parameters
                sample_rate = int(device_info['defaultSampleRate'])
                channels = min(device_info['maxInputChannels'], 2)  # Limit to 2 channels max
                self.sample_rate_var.set(str(sample_rate))
                self.channels_var.set(str(channels))
                
                # Test again with device defaults
                try:
                    test_stream = self.audio.open(
                        format=pyaudio.paInt16,
                        channels=channels,
                        rate=sample_rate,
                        input=True,
                        input_device_index=device_index,
                        frames_per_buffer=1024
                    )
                    test_stream.close()
                except Exception as e2:
                    logger.warning(f"Device defaults failed, trying fallback: {e2}")
                    # Final fallback - try common parameters
                    for fallback_rate in [44100, 48000, 16000, 8000]:
                        try:
                            test_stream = self.audio.open(
                                format=pyaudio.paInt16,
                                channels=1,  # Mono as fallback
                                rate=fallback_rate,
                                input=True,
                                input_device_index=device_index,
                                frames_per_buffer=1024
                            )
                            test_stream.close()
                            sample_rate = fallback_rate
                            channels = 1
                            self.sample_rate_var.set(str(sample_rate))
                            self.channels_var.set(str(channels))
                            break
                        except:
                            continue
            
            self.audio_stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=sample_rate,
                input=True,
                input_device_index=device_index,
                stream_callback=self.audio_callback,
                frames_per_buffer=1024
            )
            
            self.audio_stream.start_stream()
            self.audio_recording = True
            self.recording_start_time = time.time()
            self.record_button.config(text="Stop Recording")
            self.audio_status_var.set(f"Recording from: {device_name}")
            self.status_var.set("Audio recording started")
            
            # Show recording duration
            self.duration_label.pack(pady=5)
            self.update_recording_duration()
            
            # Start visualization update
            self.update_visualization()
            
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            messagebox.showerror("Error", f"Failed to start recording: {e}\n\nTry checking your audio device settings.")
    
    def stop_recording(self):
        """Stop audio recording"""
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None
        
        if hasattr(self, 'audio'):
            self.audio.terminate()
        
        self.audio_recording = False
        self.recording_start_time = None
        self.record_button.config(text="● RECORD", state=tk.DISABLED)
        self.audio_status_var.set("Recording stopped - Audio saved")
        self.recording_duration_var.set("")
        self.duration_label.pack_forget()  # Hide duration label
        self.status_var.set("Audio recording stopped")
        
        # Enable playback button if we have recorded audio
        if len(self.audio_buffer) > 0:
            self.playback_button.config(state=tk.NORMAL)
    
    def start_playback(self):
        """Start playing the recorded audio through speakers"""
        try:
            if len(self.audio_buffer) == 0:
                messagebox.showwarning("Warning", "No audio recorded to play back!")
                return
            
            # Convert recorded audio to numpy array
            audio_data = np.array(list(self.audio_buffer), dtype=np.int16)
            
            # Initialize PyAudio for playback
            self.playback_audio = pyaudio.PyAudio()
            
            # Get default output device
            output_device = self.playback_audio.get_default_output_device_info()
            
            # Create playback stream
            self.playback_stream = self.playback_audio.open(
                format=pyaudio.paInt16,
                channels=1,  # Mono playback
                rate=16000,  # Default sample rate
                output=True,
                output_device_index=output_device['index']
            )
            
            # Start playback in a separate thread
            self.playback_thread = threading.Thread(target=self._playback_thread)
            self.playback_thread.daemon = True
            self.playback_thread.start()
            
            self.audio_playing = True
            self.playback_button.config(text="⏹ STOP")
            self.audio_status_var.set("Playing recorded audio...")
            self.status_var.set("Audio playback started")
            
        except Exception as e:
            logger.error(f"Error starting playback: {e}")
            messagebox.showerror("Error", f"Failed to start playback: {e}")
    
    def stop_playback(self):
        """Stop audio playback"""
        self.audio_playing = False
        
        if hasattr(self, 'playback_stream') and self.playback_stream:
            self.playback_stream.stop_stream()
            self.playback_stream.close()
            self.playback_stream = None
        
        if hasattr(self, 'playback_audio') and self.playback_audio:
            self.playback_audio.terminate()
            self.playback_audio = None
        
        self.playback_button.config(text="▶ PLAYBACK")
        self.audio_status_var.set("Playback stopped")
        self.status_var.set("Audio playback stopped")
    
    def _playback_thread(self):
        """Playback thread function"""
        try:
            # Convert recorded audio to bytes
            audio_data = np.array(list(self.audio_buffer), dtype=np.int16)
            audio_bytes = audio_data.tobytes()
            
            # Play audio in chunks
            chunk_size = 1024
            for i in range(0, len(audio_bytes), chunk_size * 2):  # *2 because int16 is 2 bytes
                if not self.audio_playing:
                    break
                
                chunk = audio_bytes[i:i + chunk_size * 2]
                if len(chunk) > 0:
                    self.playback_stream.write(chunk)
            
            # Playback finished
            self.root.after(0, self._playback_finished)
            
        except Exception as e:
            logger.error(f"Error in playback thread: {e}")
            self.root.after(0, self._playback_finished)
    
    def _playback_finished(self):
        """Called when playback finishes"""
        self.audio_playing = False
        self.playback_button.config(text="▶ PLAYBACK")
        self.audio_status_var.set("Playback finished")
        self.status_var.set("Audio playback finished")
    
    def update_recording_duration(self):
        """Update recording duration display"""
        if self.audio_recording and self.recording_start_time and not self.audio_paused:
            elapsed = time.time() - self.recording_start_time - self.recording_paused_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            self.recording_duration_var.set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # Schedule next update
            self.recording_duration_timer = self.root.after(1000, self.update_recording_duration)
    
    def pause_recording(self):
        """Pause recording"""
        if self.audio_recording and not self.audio_paused:
            self.audio_paused = True
            self.recording_paused_time += time.time() - self.recording_start_time
            self.pause_button.config(text="▶ RESUME")
            self.recording_status_var.set("Paused")
            self.status_var.set("Recording paused")
    
    def play_pause_recording(self):
        """Toggle recording pause/resume"""
        if self.audio_paused:
            self.audio_paused = False
            self.recording_start_time = time.time()
            self.pause_button.config(text="⏸ PAUSE")
            self.recording_status_var.set("Recording...")
            self.status_var.set("Recording resumed")
            self.update_recording_duration()
        else:
            self.pause_recording()
    
    def rewind_recording(self):
        """Rewind recording (not implemented for live recording)"""
        self.status_var.set("Rewind not available for live recording")
    
    def forward_recording(self):
        """Forward recording (not implemented for live recording)"""
        self.status_var.set("Forward not available for live recording")
    
    def clear_recording(self):
        """Clear current recording"""
        if messagebox.askyesno("Confirm", "Clear current recording?"):
            self.audio_buffer.clear()
            self.recording_duration_var.set("00:00:00")
            self.recording_paused_time = 0
            self.status_var.set("Recording cleared")
    
    def rewind_playback(self):
        """Rewind playback"""
        if self.loaded_audio_data:
            self.playback_position = max(0, self.playback_position - 10000)  # Rewind 10k samples
            self.update_playback_position()
    
    def forward_playback(self):
        """Forward playback"""
        if self.loaded_audio_data:
            self.playback_position = min(len(self.loaded_audio_data), self.playback_position + 10000)  # Forward 10k samples
            self.update_playback_position()
    
    def pause_playback(self):
        """Pause playback"""
        if self.audio_playing:
            self.playback_paused = True
            self.status_var.set("Playback paused")
    
    def update_playback_position(self):
        """Update playback position display"""
        if self.loaded_audio_data:
            # Convert sample position to time
            sample_rate = 16000  # Default sample rate
            position_seconds = self.playback_position / sample_rate
            hours = int(position_seconds // 3600)
            minutes = int((position_seconds % 3600) // 60)
            seconds = int(position_seconds % 60)
            self.playback_position_var.set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def load_audio_file(self):
        """Load audio file for playback"""
        filename = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with wave.open(filename, 'rb') as wav_file:
                    self.loaded_audio_data = wav_file.readframes(wav_file.getnframes())
                    self.loaded_audio_file = filename
                    self.current_file_var.set(f"Loaded: {os.path.basename(filename)}")
                    self.play_button.config(state=tk.NORMAL)
                    self.status_var.set(f"Audio file loaded: {filename}")
            except Exception as e:
                logger.error(f"Error loading audio file: {e}")
                messagebox.showerror("Error", f"Failed to load audio file: {e}")
    
    
    
    
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Audio stream callback"""
        if self.audio_recording or self.audio_listening:
            # Convert bytes to numpy array
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            self.audio_data_queue.put(audio_data)
            
            # Store in time pattern buffer for long-term visualization
            self.time_pattern_buffer.extend(audio_data)
            
            # Initialize pattern start time if not set
            if self.pattern_start_time is None:
                self.pattern_start_time = time.time()
            
            # Debug logging (only log occasionally to avoid spam)
            if len(self.time_pattern_buffer) % 1000 == 0:
                logger.info(f"Audio callback: {len(audio_data)} samples, total buffer: {len(self.time_pattern_buffer)}")
        return (in_data, pyaudio.paContinue)
    
    def update_visualization(self):
        """Update real-time waveform visualization with time-based patterns"""
        if not (self.audio_recording or self.audio_listening):
            return
        
        try:
            # Get audio data from queue
            audio_data = None
            while not self.audio_data_queue.empty():
                audio_data = self.audio_data_queue.get()
                self.audio_buffer.extend(audio_data)
            
            if audio_data is not None and len(audio_data) > 0:
                # Calculate max amplitude for display
                max_amplitude = np.max(np.abs(audio_data))
                
                # Update all three visualization panels
                if len(self.audio_buffer) > 100:  # Only update if we have enough data
                    channels = int(self.channels_var.get())
                    
                    # Panel 1: Real-time waveform (recent data)
                    recent_data = list(self.audio_buffer)[-2000:]  # Last 2000 samples
                    self._plot_realtime_waveform(recent_data, channels)
                    
                    # Panel 2: Time pattern (longer view)
                    if len(self.time_pattern_buffer) > 1000:
                        self._plot_time_pattern()
                    
                    # Panel 3: Amplitude envelope over time
                    if len(self.time_pattern_buffer) > 100:
                        self._plot_amplitude_envelope()
                    
                    # Add real-time info
                    current_time = time.strftime("%H:%M:%S")
                    elapsed_time = time.time() - self.pattern_start_time if self.pattern_start_time else 0
                    info_text = f"Live Audio - {current_time} | Duration: {elapsed_time:.1f}s | Max: {max_amplitude} | Samples: {len(recent_data)}"
                    self.waveform_fig.suptitle(info_text, fontsize=10, y=0.98)
                    
                    self.waveform_fig.tight_layout()
                    self.waveform_fig.canvas.draw()
        
        except Exception as e:
            logger.error(f"Error updating visualization: {e}")
        
        # Schedule next update
        if self.audio_recording or self.audio_listening:
            self.root.after(50, self.update_visualization)
    
    def _plot_realtime_waveform(self, recent_data, channels):
        """Plot real-time waveform in top panel"""
        self.waveform_ax1.clear()
        
        if channels == 1:
            # Mono audio
            self.waveform_ax1.plot(recent_data, color='blue', linewidth=0.5)
            self.waveform_ax1.set_title("Real-time Audio (Mono)", fontsize=10)
        else:
            # Stereo audio - separate channels
            if len(recent_data) >= 2:
                left_channel = recent_data[::2]
                right_channel = recent_data[1::2]
                min_len = min(len(left_channel), len(right_channel))
                left_channel = left_channel[:min_len]
                right_channel = right_channel[:min_len]
                
                self.waveform_ax1.plot(left_channel, color='blue', linewidth=0.5, label='Left')
                self.waveform_ax1.plot(right_channel, color='red', linewidth=0.5, label='Right')
                self.waveform_ax1.legend(fontsize=8)
                self.waveform_ax1.set_title("Real-time Audio (Stereo)", fontsize=10)
            else:
                self.waveform_ax1.plot(recent_data, color='blue', linewidth=0.5)
                self.waveform_ax1.set_title("Real-time Audio", fontsize=10)
        
        self.waveform_ax1.set_ylabel("Amplitude")
        self.waveform_ax1.set_ylim(-32768, 32768)
        self.waveform_ax1.grid(True, alpha=0.3)
    
    def _plot_time_pattern(self):
        """Plot time-based pattern in middle panel"""
        self.waveform_ax2.clear()
        
        # Get time pattern data
        pattern_data = list(self.time_pattern_buffer)
        logger.info(f"Time pattern buffer size: {len(pattern_data)}")
        if len(pattern_data) < 100:
            logger.info("Not enough data in time pattern buffer")
            return
        
        # Create time axis
        sample_rate = int(self.sample_rate_var.get())
        time_axis = np.arange(len(pattern_data)) / sample_rate
        
        # Downsample for better performance with large datasets
        if len(pattern_data) > 10000:
            step = len(pattern_data) // 10000
            pattern_data = pattern_data[::step]
            time_axis = time_axis[::step]
        
        # Plot the pattern
        self.waveform_ax2.plot(time_axis, pattern_data, color='green', linewidth=0.3, alpha=0.7)
        self.waveform_ax2.set_title("Audio Pattern Over Time", fontsize=10)
        self.waveform_ax2.set_ylabel("Amplitude")
        self.waveform_ax2.set_xlabel("Time (seconds)")
        self.waveform_ax2.set_ylim(-32768, 32768)
        self.waveform_ax2.grid(True, alpha=0.3)
        
        # Add time markers
        if len(time_axis) > 0:
            max_time = time_axis[-1]
            if max_time > 10:
                # Add 10-second markers
                for i in range(0, int(max_time), 10):
                    self.waveform_ax2.axvline(x=i, color='red', alpha=0.3, linestyle='--')
    
    def _plot_amplitude_envelope(self):
        """Plot amplitude envelope over time in bottom panel"""
        self.waveform_ax3.clear()
        
        # Get time pattern data
        pattern_data = list(self.time_pattern_buffer)
        if len(pattern_data) < 100:
            return
        
        # Calculate amplitude envelope
        window_size = 1000  # Samples per window
        envelope = []
        time_points = []
        sample_rate = int(self.sample_rate_var.get())
        
        for i in range(0, len(pattern_data), window_size):
            window = pattern_data[i:i+window_size]
            if len(window) > 0:
                # Calculate RMS (Root Mean Square) for envelope
                rms = np.sqrt(np.mean(np.square(window)))
                envelope.append(rms)
                time_points.append(i / sample_rate)
        
        if len(envelope) > 1:
            # Plot envelope
            self.waveform_ax3.plot(time_points, envelope, color='purple', linewidth=1.5)
            self.waveform_ax3.fill_between(time_points, envelope, alpha=0.3, color='purple')
            self.waveform_ax3.set_title("Amplitude Envelope Over Time", fontsize=10)
            self.waveform_ax3.set_ylabel("RMS Amplitude")
            self.waveform_ax3.set_xlabel("Time (seconds)")
            self.waveform_ax3.grid(True, alpha=0.3)
            
            # Add dynamic range indicators
            if len(envelope) > 0:
                max_env = max(envelope)
                self.waveform_ax3.axhline(y=max_env, color='red', alpha=0.5, linestyle='--', label=f'Peak: {max_env:.0f}')
                self.waveform_ax3.legend(fontsize=8)
    
    def generate_histogram(self):
        """Generate audio histogram"""
        if not self.audio_buffer:
            messagebox.showwarning("Warning", "No audio data available for histogram")
            return
        
        try:
            # Convert buffer to numpy array
            audio_array = np.array(list(self.audio_buffer))
            
            # Generate histogram
            self.ax2.clear()
            self.ax2.hist(audio_array, bins=50, alpha=0.7, color='blue')
            self.ax2.set_title("Audio Amplitude Histogram")
            self.ax2.set_xlabel("Amplitude")
            self.ax2.set_ylabel("Frequency")
            
            # Calculate statistics
            mean_val = np.mean(audio_array)
            std_val = np.std(audio_array)
            max_val = np.max(np.abs(audio_array))
            
            self.ax2.axvline(mean_val, color='red', linestyle='--', label=f'Mean: {mean_val:.2f}')
            self.ax2.axvline(mean_val + std_val, color='orange', linestyle='--', label=f'+1σ: {mean_val + std_val:.2f}')
            self.ax2.axvline(mean_val - std_val, color='orange', linestyle='--', label=f'-1σ: {mean_val - std_val:.2f}')
            self.ax2.legend()
            
            # Update parameter effects plot
            self.ax4.clear()
            self.ax4.text(0.1, 0.8, f"Audio Statistics:", fontsize=12, weight='bold')
            self.ax4.text(0.1, 0.7, f"Mean: {mean_val:.2f}", fontsize=10)
            self.ax4.text(0.1, 0.6, f"Std Dev: {std_val:.2f}", fontsize=10)
            self.ax4.text(0.1, 0.5, f"Max Amplitude: {max_val:.2f}", fontsize=10)
            self.ax4.text(0.1, 0.4, f"Samples: {len(audio_array)}", fontsize=10)
            self.ax4.set_xlim(0, 1)
            self.ax4.set_ylim(0, 1)
            self.ax4.axis('off')
            self.ax4.set_title("Audio Statistics")
            
            self.fig.canvas.draw()
            
        except Exception as e:
            logger.error(f"Error generating histogram: {e}")
            messagebox.showerror("Error", f"Failed to generate histogram: {e}")
    
    def clear_audio_data(self):
        """Clear audio data buffer"""
        self.audio_buffer.clear()
        self.ax2.clear()
        self.ax4.clear()
        self.fig.canvas.draw()
        self.status_var.set("Audio data cleared")
    
    def save_recording(self):
        """Save recorded audio to file"""
        if not self.audio_buffer:
            messagebox.showwarning("Warning", "No audio data to save")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                audio_array = np.array(list(self.audio_buffer), dtype=np.int16)
                
                with wave.open(filename, 'wb') as wav_file:
                    wav_file.setnchannels(int(self.channels_var.get()))
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(int(self.sample_rate_var.get()))
                    wav_file.writeframes(audio_array.tobytes())
                
                self.status_var.set(f"Audio saved to {filename}")
                messagebox.showinfo("Success", f"Audio saved to {filename}")
                
            except Exception as e:
                logger.error(f"Error saving audio: {e}")
                messagebox.showerror("Error", f"Failed to save audio: {e}")
    
    def apply_all_parameters(self):
        """Apply all parameter changes to device"""
        if not self.device_connected:
            messagebox.showerror("Error", "Device not connected!")
            return
        
        def apply_parameters():
            self.status_var.set("Applying parameters...")
            
            # Get current parameter values from UI
            params_to_apply = {}
            for param_name in self.current_params.keys():
                var_name = f"{param_name.lower()}_var"
                if hasattr(self, var_name):
                    var = getattr(self, var_name)
                    params_to_apply[param_name] = var.get()
            
            # Apply parameters
            for param_name, value in params_to_apply.items():
                result = self.run_xvf_command(param_name, value)
                if result:
                    self.current_params[param_name] = value
                    logger.info(f"Applied {param_name} = {value}")
                else:
                    logger.error(f"Failed to apply {param_name}")
            
            self.status_var.set("Parameters applied successfully")
        
        threading.Thread(target=apply_parameters, daemon=True).start()
    
    def reset_parameters(self):
        """Reset parameters to defaults"""
        defaults = {
            'AUDIO_MGR_MIC_GAIN': 90,
            'AUDIO_MGR_REF_GAIN': 8.0,
            'AUDIO_MGR_SYS_DELAY': -32,
            'PP_AGCGAIN': 2.0,
            'PP_AGCMAXGAIN': 64.0,
            'PP_FMIN_SPEINDEX': 1300.0,
            'AEC_ASROUTGAIN': 1.0
        }
        
        for param_name, default_value in defaults.items():
            var_name = f"{param_name.lower()}_var"
            if hasattr(self, var_name):
                var = getattr(self, var_name)
                var.set(default_value)
        
        self.status_var.set("Parameters reset to defaults")
    
    def save_configuration(self):
        """Save current configuration to device"""
        if not self.device_connected:
            messagebox.showerror("Error", "Device not connected!")
            return
        
        result = self.run_xvf_command("SAVE_CONFIGURATION", 1)
        if result:
            self.status_var.set("Configuration saved to device")
            messagebox.showinfo("Success", "Configuration saved to device")
        else:
            messagebox.showerror("Error", "Failed to save configuration")
    
    def clear_configuration(self):
        """Clear device configuration"""
        if not self.device_connected:
            messagebox.showerror("Error", "Device not connected!")
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to clear the device configuration?"):
            result = self.run_xvf_command("CLEAR_CONFIGURATION", 1)
            if result:
                self.status_var.set("Configuration cleared")
                messagebox.showinfo("Success", "Configuration cleared")
            else:
                messagebox.showerror("Error", "Failed to clear configuration")
    
    def set_led_effect(self):
        """Set LED effect"""
        if not self.device_connected:
            messagebox.showerror("Error", "Device not connected!")
            return
        
        effect = int(self.led_effect_var.get().split()[0])
        result = self.run_xvf_command("LED_EFFECT", effect)
        if result:
            self.status_var.set(f"LED effect set to {effect}")
        else:
            messagebox.showerror("Error", "Failed to set LED effect")
    
    def set_led_color(self):
        """Set LED color"""
        if not self.device_connected:
            messagebox.showerror("Error", "Device not connected!")
            return
        
        try:
            color = int(self.led_color_var.get(), 16)
            result = self.run_xvf_command("LED_COLOR", color)
            if result:
                self.status_var.set(f"LED color set to {self.led_color_var.get()}")
            else:
                messagebox.showerror("Error", "Failed to set LED color")
        except ValueError:
            messagebox.showerror("Error", "Invalid color format. Use hex format (e.g., 0xff0000)")
    
    def apply_led_settings(self):
        """Apply all LED settings"""
        if not self.device_connected:
            messagebox.showerror("Error", "Device not connected!")
            return
        
        def apply_settings():
            try:
                # Set effect
                effect_str = self.led_effect_var.get()
                if " - " in effect_str:
                    effect = int(effect_str.split(" - ")[0])
                else:
                    effect = int(effect_str)
                result = self.run_xvf_command("LED_EFFECT", effect)
                if result:
                    logger.info(f"LED effect set to {effect}")
                
                # Set color
                color_str = self.led_color_var.get()
                if color_str.startswith("0x"):
                    color = int(color_str, 16)
                else:
                    color = int(color_str, 16)
                result = self.run_xvf_command("LED_COLOR", color)
                if result:
                    logger.info(f"LED color set to {color_str}")
                
                # Set brightness
                brightness = int(float(self.led_brightness_var.get()))
                result = self.run_xvf_command("LED_BRIGHTNESS", brightness)
                if result:
                    logger.info(f"LED brightness set to {brightness}")
                
                # Set speed
                speed = int(float(self.led_speed_var.get()))
                result = self.run_xvf_command("LED_SPEED", speed)
                if result:
                    logger.info(f"LED speed set to {speed}")
                
                self.status_var.set("LED settings applied successfully")
                
            except ValueError as e:
                logger.error(f"Invalid LED parameter: {e}")
                messagebox.showerror("Error", f"Invalid LED parameter: {e}")
            except Exception as e:
                logger.error(f"Error applying LED settings: {e}")
                messagebox.showerror("Error", f"Error applying LED settings: {e}")
        
        threading.Thread(target=apply_settings, daemon=True).start()
    
    def read_gpi_values(self):
        """Read GPI values"""
        if not self.device_connected:
            messagebox.showerror("Error", "Device not connected!")
            return
        
        result = self.run_xvf_command("GPI_READ_VALUES")
        if result:
            self.gpi_values_var.set(result)
            self.status_var.set("GPI values read")
        else:
            messagebox.showerror("Error", "Failed to read GPI values")
    
    def read_gpo_values(self):
        """Read GPO values"""
        if not self.device_connected:
            messagebox.showerror("Error", "Device not connected!")
            return
        
        result = self.run_xvf_command("GPO_READ_VALUES")
        if result:
            self.gpo_values_var.set(result)
            self.status_var.set("GPO values read")
        else:
            messagebox.showerror("Error", "Failed to read GPO values")
    
    def set_gpo_value(self):
        """Set GPO value"""
        if not self.device_connected:
            messagebox.showerror("Error", "Device not connected!")
            return
        
        try:
            pin = int(self.gpo_pin_var.get())
            value = int(self.gpo_value_var.get())
            
            result = self.run_xvf_command("GPO_WRITE_VALUE", pin, value)
            if result:
                self.status_var.set(f"GPO pin {pin} set to {value}")
            else:
                messagebox.showerror("Error", "Failed to set GPO value")
        except ValueError:
            messagebox.showerror("Error", "Invalid pin or value")
    
    def check_aec_status(self):
        """Check AEC status"""
        if not self.device_connected:
            messagebox.showerror("Error", "Device not connected!")
            return
        
        result = self.run_xvf_command("AEC_AECCONVERGED")
        if result:
            converged = result.strip() == "1"
            converged_text = "Yes" if converged else "No"
            self.aec_status_var.set(f"AEC Converged: {converged_text}")
            self.status_var.set("AEC status checked")
            
            # Store convergence data for visualization
            self.aec_convergence_history.append({
                'converged': 1 if converged else 0,
                'timestamp': time.time()
            })
            self.update_aec_visualization()
        else:
            messagebox.showerror("Error", "Failed to check AEC status")
    
    def get_speech_energy(self):
        """Get speech energy values"""
        if not self.device_connected:
            messagebox.showerror("Error", "Device not connected!")
            return
        
        result = self.run_xvf_command("AEC_SPENERGY_VALUES")
        if result:
            self.speech_energy_var.set(result)
            self.status_var.set("Speech energy values retrieved")
            
            # Parse and store energy values for visualization
            try:
                # Extract only the numeric values, skip the device init message
                lines = result.strip().split('\n')
                data_line = None
                for line in lines:
                    if line.startswith('AEC_SPENERGY_VALUES'):
                        data_line = line
                        break
                
                if data_line:
                    # Extract values after the command name
                    values_str = data_line.replace('AEC_SPENERGY_VALUES', '').strip()
                    energy_values = [float(x) for x in values_str.split()]
                    if len(energy_values) >= 4:
                        self.aec_energy_history.append({
                            'beam1': energy_values[0],
                            'beam2': energy_values[1], 
                            'free_running': energy_values[2],
                            'auto_select': energy_values[3],
                            'timestamp': time.time()
                        })
                        self.update_aec_visualization()
            except (ValueError, IndexError) as e:
                logger.warning(f"Could not parse speech energy values: {e}")
        else:
            messagebox.showerror("Error", "Failed to get speech energy values")
    
    def get_azimuth_values(self):
        """Get azimuth values"""
        if not self.device_connected:
            messagebox.showerror("Error", "Device not connected!")
            return
        
        result = self.run_xvf_command("AEC_AZIMUTH_VALUES")
        if result:
            self.azimuth_values_var.set(result)
            self.status_var.set("Azimuth values retrieved")
            
            # Parse and store azimuth values for visualization
            try:
                # Extract only the numeric values, skip the device init message
                lines = result.strip().split('\n')
                data_line = None
                for line in lines:
                    if line.startswith('AEC_AZIMUTH_VALUES'):
                        data_line = line
                        break
                
                if data_line:
                    # Extract values after the command name, handle both radians and degrees
                    values_str = data_line.replace('AEC_AZIMUTH_VALUES', '').strip()
                    # Split by spaces and extract only numeric values (skip degree text)
                    parts = values_str.split()
                    azimuth_values = []
                    for part in parts:
                        try:
                            # Try to convert to float, skip if it contains non-numeric text
                            if '(' not in part and 'deg' not in part:
                                azimuth_values.append(float(part))
                        except ValueError:
                            continue
                    
                    if len(azimuth_values) >= 4:
                        self.aec_azimuth_history.append({
                            'beam1': azimuth_values[0],
                            'beam2': azimuth_values[1],
                            'free_running': azimuth_values[2], 
                            'auto_select': azimuth_values[3],
                            'timestamp': time.time()
                        })
                        self.update_aec_visualization()
            except (ValueError, IndexError) as e:
                logger.warning(f"Could not parse azimuth values: {e}")
        else:
            messagebox.showerror("Error", "Failed to get azimuth values")
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh for AEC data"""
        if self.auto_refresh_var.get():
            self.auto_refresh_aec_data()
        else:
            self.status_var.set("Auto-refresh disabled")
    
    def auto_refresh_aec_data(self):
        """Auto-refresh AEC data"""
        if self.auto_refresh_var.get() and self.device_connected:
            self.get_speech_energy()
            self.get_azimuth_values()
            self.check_aec_status()
            
            # Schedule next refresh
            self.root.after(1000, self.auto_refresh_aec_data)
    
    def update_aec_visualization(self):
        """Update AEC real-time visualization"""
        try:
            # Clear all plots
            self.aec_ax1.clear()
            self.aec_ax2.clear()
            self.aec_ax3.clear()
            self.aec_ax4.clear()
            
            # Plot 1: Speech Energy over time (focused on changes)
            if self.aec_energy_history:
                # Convert timestamps to relative time
                start_time = self.aec_energy_history[0]['timestamp']
                timestamps = [(entry['timestamp'] - start_time) for entry in self.aec_energy_history]
                
                beam1_energy = [entry['beam1'] for entry in self.aec_energy_history]
                beam2_energy = [entry['beam2'] for entry in self.aec_energy_history]
                free_running_energy = [entry['free_running'] for entry in self.aec_energy_history]
                auto_select_energy = [entry['auto_select'] for entry in self.aec_energy_history]
                
                self.aec_ax1.plot(timestamps, beam1_energy, label='Beam 1', color='blue', linewidth=2)
                self.aec_ax1.plot(timestamps, beam2_energy, label='Beam 2', color='green', linewidth=2)
                self.aec_ax1.plot(timestamps, free_running_energy, label='Free Running', color='orange', linewidth=2)
                self.aec_ax1.plot(timestamps, auto_select_energy, label='Auto Select', color='red', linewidth=2)
                self.aec_ax1.set_title('Speech Energy Changes Over Time', fontsize=12, fontweight='bold')
                self.aec_ax1.set_ylabel('Energy Level', fontsize=10)
                self.aec_ax1.set_xlabel('Time (seconds)', fontsize=10)
                self.aec_ax1.legend(fontsize=8)
                self.aec_ax1.grid(True, alpha=0.3)
                
                # Add current values as text
                if len(beam1_energy) > 0:
                    current_values = f"Current: B1={beam1_energy[-1]:.0f}, B2={beam2_energy[-1]:.0f}, FR={free_running_energy[-1]:.0f}, AS={auto_select_energy[-1]:.0f}"
                    self.aec_ax1.text(0.02, 0.98, current_values, transform=self.aec_ax1.transAxes, 
                                    fontsize=8, verticalalignment='top', 
                                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            # Plot 2: Azimuth Values over time (focused on changes)
            if self.aec_azimuth_history:
                # Convert timestamps to relative time
                start_time = self.aec_azimuth_history[0]['timestamp']
                timestamps = [(entry['timestamp'] - start_time) for entry in self.aec_azimuth_history]
                
                beam1_azimuth = [entry['beam1'] for entry in self.aec_azimuth_history]
                beam2_azimuth = [entry['beam2'] for entry in self.aec_azimuth_history]
                free_running_azimuth = [entry['free_running'] for entry in self.aec_azimuth_history]
                auto_select_azimuth = [entry['auto_select'] for entry in self.aec_azimuth_history]
                
                self.aec_ax2.plot(timestamps, beam1_azimuth, label='Beam 1', color='blue', linewidth=2)
                self.aec_ax2.plot(timestamps, beam2_azimuth, label='Beam 2', color='green', linewidth=2)
                self.aec_ax2.plot(timestamps, free_running_azimuth, label='Free Running', color='orange', linewidth=2)
                self.aec_ax2.plot(timestamps, auto_select_azimuth, label='Auto Select', color='red', linewidth=2)
                self.aec_ax2.set_title('Azimuth Changes Over Time', fontsize=12, fontweight='bold')
                self.aec_ax2.set_ylabel('Azimuth (radians)', fontsize=10)
                self.aec_ax2.set_xlabel('Time (seconds)', fontsize=10)
                self.aec_ax2.legend(fontsize=8)
                self.aec_ax2.grid(True, alpha=0.3)
                
                # Add current values as text
                if len(beam1_azimuth) > 0:
                    current_values = f"Current: B1={beam1_azimuth[-1]:.3f}, B2={beam2_azimuth[-1]:.3f}, FR={free_running_azimuth[-1]:.3f}, AS={auto_select_azimuth[-1]:.3f}"
                    self.aec_ax2.text(0.02, 0.98, current_values, transform=self.aec_ax2.transAxes, 
                                    fontsize=8, verticalalignment='top', 
                                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            # Plot 3: AEC Convergence Status
            if self.aec_convergence_history:
                start_time = self.aec_convergence_history[0]['timestamp']
                timestamps = [(entry['timestamp'] - start_time) for entry in self.aec_convergence_history]
                convergence = [entry['converged'] for entry in self.aec_convergence_history]
                
                self.aec_ax3.plot(timestamps, convergence, 'o-', color='purple', linewidth=2, markersize=4)
                self.aec_ax3.set_title('AEC Convergence Status', fontsize=12, fontweight='bold')
                self.aec_ax3.set_ylabel('Converged (1=Yes, 0=No)', fontsize=10)
                self.aec_ax3.set_xlabel('Time (seconds)', fontsize=10)
                self.aec_ax3.set_ylim(-0.1, 1.1)
                self.aec_ax3.grid(True, alpha=0.3)
                
                # Add current status
                if len(convergence) > 0:
                    status = "CONVERGED" if convergence[-1] == 1 else "NOT CONVERGED"
                    color = 'green' if convergence[-1] == 1 else 'red'
                    self.aec_ax3.text(0.02, 0.98, f"Status: {status}", transform=self.aec_ax3.transAxes, 
                                    fontsize=10, fontweight='bold', color=color, verticalalignment='top',
                                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            # Plot 4: Energy Changes Over Time (line chart)
            if self.aec_energy_history:
                # Convert timestamps to relative time
                start_time = self.aec_energy_history[0]['timestamp']
                timestamps = [(entry['timestamp'] - start_time) for entry in self.aec_energy_history]
                
                beam1_energy = [entry['beam1'] for entry in self.aec_energy_history]
                beam2_energy = [entry['beam2'] for entry in self.aec_energy_history]
                free_running_energy = [entry['free_running'] for entry in self.aec_energy_history]
                auto_select_energy = [entry['auto_select'] for entry in self.aec_energy_history]
                
                self.aec_ax4.plot(timestamps, beam1_energy, label='Beam 1', color='blue', linewidth=2)
                self.aec_ax4.plot(timestamps, beam2_energy, label='Beam 2', color='green', linewidth=2)
                self.aec_ax4.plot(timestamps, free_running_energy, label='Free Running', color='orange', linewidth=2)
                self.aec_ax4.plot(timestamps, auto_select_energy, label='Auto Select', color='red', linewidth=2)
                self.aec_ax4.set_title('Energy Changes Over Time', fontsize=12, fontweight='bold')
                self.aec_ax4.set_ylabel('Energy Level', fontsize=10)
                self.aec_ax4.set_xlabel('Time (seconds)', fontsize=10)
                self.aec_ax4.legend(fontsize=8)
                self.aec_ax4.grid(True, alpha=0.3)
                
                # Add current values as text
                if len(beam1_energy) > 0:
                    current_values = f"Current: B1={beam1_energy[-1]:.0f}, B2={beam2_energy[-1]:.0f}, FR={free_running_energy[-1]:.0f}, AS={auto_select_energy[-1]:.0f}"
                    self.aec_ax4.text(0.02, 0.98, current_values, transform=self.aec_ax4.transAxes, 
                                    fontsize=8, verticalalignment='top', 
                                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            # Update the canvas
            self.aec_fig.tight_layout()
            self.aec_canvas.draw()
            
        except Exception as e:
            logger.error(f"Error updating AEC visualization: {e}")
    
    def refresh_audio_devices(self):
        """Refresh the list of available audio devices"""
        try:
            if hasattr(self, 'audio'):
                self.audio.terminate()
            
            self.audio = pyaudio.PyAudio()
            devices = []
            self.device_list = []
            
            for i in range(self.audio.get_device_count()):
                device_info = self.audio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:  # Only input devices
                    device_name = device_info['name']
                    channels = device_info['maxInputChannels']
                    sample_rate = device_info['defaultSampleRate']
                    device_str = f"{device_name} (Channels: {channels}, Rate: {sample_rate})"
                    devices.append(device_str)
                    self.device_list.append({
                        'index': i,
                        'name': device_name,
                        'channels': channels,
                        'sample_rate': sample_rate,
                        'info': device_info
                    })
            
            self.device_var.set('')
            self.device_combo['values'] = devices
            
            # Auto-select reSpeaker if available
            for i, device in enumerate(devices):
                if 'reSpeaker' in device or 'XVF3800' in device:
                    self.device_var.set(device)
                    self.selected_device_index = self.device_list[i]['index']
                    logger.info(f"Auto-selected device: {device}")
                    break
            
            if not devices:
                self.device_var.set("No input devices found")
                self.selected_device_index = None
            
            # Don't terminate audio here - keep it for later use
            
        except Exception as e:
            logger.error(f"Error refreshing audio devices: {e}")
            self.device_var.set("Error loading devices")
            self.selected_device_index = None
    
    def on_device_selected(self, event):
        """Handle audio device selection"""
        try:
            selected_text = self.device_var.get()
            if selected_text and selected_text != "No input devices found" and selected_text != "Error loading devices":
                # Find the device index
                for i, device in enumerate(self.device_list):
                    device_str = f"{device['name']} (Channels: {device['channels']}, Rate: {device['sample_rate']})"
                    if device_str == selected_text:
                        self.selected_device_index = device['index']
                        logger.info(f"Selected audio device: {device['name']} (Index: {device['index']})")
                        break
        except Exception as e:
            logger.error(f"Error selecting device: {e}")


def main():
    """Main application entry point"""
    # Check for required dependencies
    try:
        import numpy
        import matplotlib
        import pyaudio
    except ImportError as e:
        print(f"Missing required dependency: {e}")
        print("Please install required packages:")
        print("pip install numpy matplotlib pyaudio")
        return
    
    root = tk.Tk()
    app = XVF3800DiagnosticApp(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Application interrupted by user")
    finally:
        # Cleanup
        if app.audio_recording:
            app.stop_recording()

if __name__ == "__main__":
    main()
