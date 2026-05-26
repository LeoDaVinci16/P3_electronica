# SCADA Micro-xarxa: LED Load Control Documentation

This project implements a Micro-grid SCADA system where physical LEDs are used to represent electrical loads (Red: Critical, Blue/Green: Non-critical). The LEDs are controlled via PWM through transistors connected to the physical DC bus.

## Hardware Configuration

### ESP32 Pin Mapping
| Load Color | Load Priority | ESP32 Pin | Control Signal |
| :--- | :--- | :--- | :--- |
| **Red** | Critical | Pin 2 | PWM (1kHz) |
| **Blue** | Variable (Shed @ 36V) | Pin 4 | PWM (1kHz) |
| **Green** | Variable + Safety Sink | Pin 5 | PWM (1kHz) |

### Electronic Interface
Because the LEDs are powered by the hardware DC bus (which can vary between 0-50V), they are connected via transistors (acting as low-side switches). The ESP32 PWM pins drive the base/gate of the transistors to control the effective brightness (power consumption) of each load.

## Software Control Flow

The control of these LEDs follows a five-step process:

1.  **User Input (GUI):** The user adjusts the horizontal sliders in the "Potència de sortida" section of the SCADA. These sliders provide a percentage value (0 to 100%).
2.  **Logic Processing (Brain):** The `brain.py` module evaluates the system state (Bus Voltage). If the voltage drops below safe thresholds (e.g., 30V), it performs "Load Shedding," marking non-critical loads (Blue/Green) as unserved (`served = False`).
3.  **Scaling (Main):** In `main.py`, the percentage from the slider is converted to an 8-bit integer (0-255) for serial transmission. If a load has been shed by the Brain, its PWM value is forced to 0.
    *   `pwm_r = int(slider_val * 2.55) if served else 0`
4.  **Communication (Serial):** The `control_esp32.py` module sends specific character-prefixed commands over the serial port:
    *   `R` for Red, `L` for bLue, `G` for Green.
5.  **Firmware Execution (ESP32):** The `uControl_0.py` firmware receives the 8-bit value, scales it to the ESP32's 10-bit PWM resolution (0-1023), and updates the duty cycle.
    *   `led.duty(val * 4)`

## GUI Monitoring

The GUI has been updated to reflect this hardware setup:
*   **Units:** Labels and LCDs show consumption in **% (Duty Cycle)** rather than Amperes.
*   **Visual Feedback:** The "Esquema" (Schematic) section displays the real-time duty cycle being applied to each physical LED.
*   **Historical Data:** The power balance graphs plot the duty cycle history to visualize load shedding events alongside solar and grid power.

## How to Run

1.  Connect the ESP32 via USB.
2.  Ensure the LEDs are correctly wired to Pins 2, 4, and 5 through transistors.
3.  Flash `uControl_0.py` to the ESP32.
4.  Run `main.py` on your PC:
    ```bash
    python main.py
    ```

## Safety Features
*   **Overvoltage Protection:** If the bus voltage exceeds 45V, the Photovoltaic (PV) injection is automatically cut off.
*   **Safety Dummy Load:** If the bus exceeds 45V, the **Green LED** is forced to 100% duty cycle to act as an energy sink, even if its slider is at 0 or it was previously shed.
*   **Grid Support:** If the critical load is active and the bus voltage drops, the system automatically requests power from the grid to maintain stability.

## PWM vs Visualization Clarification
Physical PWM signals on Pins 2, 4, and 5 are **binary switching signals** (0V or 3.3V). The SCADA system:
1.  **Controls the Duty Cycle:** The sliders (0-100%) define how long the signal stays at 3.3V within each 1ms cycle (1kHz).
2.  **Visualizes Effective Voltage:** The Hardware Monitor plots show a value between 0V and 3.3V. This represents the **average voltage** (e.g., 50% duty cycle = 1.65V). 
3.  **Sampling Frequency:** Since the UI updates every 50ms, it is impossible to show individual 1ms pulses. Instead, we display the "commanded duty cycle" to represent the power level sent to the LEDs.