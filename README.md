# Sistema SCADA de Balanç Energètic

Aquest projecte implementa una interfície SCADA (Supervisory Control and Data Acquisition) en temps real per gestionar un sistema energètic híbrid que consta de generació fotovoltaica (FV), una conexió a la xarxa i múltiples càrregues de consum.

El sistema està dissenyat per monitoritzar el balanç energètic i assegurar que la càrrega crítica sempre estigui alimentada mitjançant la regulació automàtica del generador de reserva.

## 🚀 Característiques

- **Gràfics en temps real**: Visualitza el balanç energètic net (Generació - Consum) utilitzant `pyqtgraph`.
- **Lògica automatitzada**: Si la generació solar és insuficient per cobrir la càrrega crítica (`Carga 1`), el sistema activa automàticament el generador dièsel i ajusta la seva sortida per satisfer el dèficit.
- **Panell de control interactiu**: Controla els nivells de consum de càrregues individuals mitjançant lliscadors.
- **Mode dual**: Admet tant la simulació local (per defecte a `control_v1.py`) com la integració de maquinari mitjançant comunicació sèrie amb un ESP32.

## 🛠️ Estructura del projecte

- `control_v1.py`: La lògica principal de l'aplicació i la gestió de la GUI.
- `control_ui_v1.py`: Classe Python generada a partir del fitxer `.ui` de Qt Designer.
- `uControl.py`: Script MicroPython per a l'ESP32 per gestionar senyals ADC/DAC i PWM.
- `ui_file.ui`: El fitxer de disseny original per a Qt Designer.

## 📋 Requisits previs

Assegureu-vos de tenir Python 3.x instal·lat. També necessitareu les següents llibreries:

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
pyrcc5 dibuix.qrc -o dibuix_rc.py
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
