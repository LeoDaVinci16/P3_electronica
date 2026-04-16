# Energy Balance SCADA System

This project implements a real-time SCADA (Supervisory Control and Data Acquisition) interface to manage a hybrid energy system consisting of Photovoltaic (PV) generation, a Diesel generator, and multiple consumer loads.

The system is designed to monitor the energy balance and ensure that critical loads are always powered by automatically regulating the backup generator.

## 🚀 Features

- **Real-time Plotting**: Visualizes the net energy balance (Generation - Consumption) using `pyqtgraph`.
- **Automated Logic**: If Solar generation is insufficient to cover the critical load (`Carga 1`), the system automatically activates the Diesel generator and adjusts its output to meet the deficit.
- **Interactive Dashboard**: Control PV generation levels and individual load consumption via sliders.
- **Dual Mode**: Supports both local simulation (default in `control_v1.py`) and hardware integration via Serial communication with an ESP32.

## 🛠️ Project Structure

- `control_v1.py`: The main application logic and GUI management.
- `control_ui_v1.py`: Python class generated from the Qt Designer `.ui` file.
- `uControl.py`: MicroPython script for the ESP32 to handle ADC/DAC and PWM signals.
- `ui_file.ui`: The original design file for Qt Designer.

## 📋 Prerequisites

Ensure you have Python 3.x installed. You will also need the following libraries:

```bash
pip install PyQt5 pyqtgraph pyserial
```

## ⚙️ Installation & Usage

### 1. UI Compilation
If you modify the `.ui` file in Qt Designer, you must re-generate the Python UI class:

```bash
pyuic5 ui_v1.ui -o control_ui_v1.py
```

### 2. Running the Simulation
To launch the SCADA interface:

```bash
python control_v1.py
```

### 3. Hardware Setup (Optional)
If using an ESP32:
1. Flash `uControl.py` to your ESP32 using Thonny or rshell.
2. Connect the ESP32 via USB.
3. Ensure `USE_SERIAL` is set to `True` in your configuration (if applicable).

## 🧠 System Logic

The core logic in `muestreo()` follows these steps every 100ms:
1. **Calculate Consumption**: Sum of all active loads ($C_1 + C_2 + C_3$).
2. **Calculate Generation**: PV power + Diesel power (if active).
3. **Critical Protection**: If Total Generation < $C_1$:
    - Automatically turn ON the Diesel generator.
    - Set Diesel output to exactly cover the missing power.
4. **Update UI**: Display the net balance on the LCD and update the real-time graph.

---
*Developed as part of the Master in Electronic Engineering (P3 Electronics).*

