import sys
from PyQt5 import QtWidgets, QtCore
from gui import GUI
from brain import Brain
from control_esp32 import ESP32Controller

print("Iniciant aplicació en mode HARDWARE REAL...")

class MainApp:
    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        
        # Inicialització de mòduls
        self.gui = GUI(show_hw=True, mode='main')
        self.gui.setWindowTitle("SCADA HARDWARE REAL - Micro-xarxa") # Set window title like hybrid.py
        self.gui.show()
        self.brain = Brain()
        self.esp32 = ESP32Controller()
        self.elapsed_time_h = 0.0 # Temps total d'execució
        self.last_v = 0.0 # Últim valor de bus llegit per fallback

        # Timer d'execució (50ms)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.run_loop)
        self.timer.start(50)
        
        # Exit
        self.gui.pushButton_3.clicked.connect(self.shutdown)

    def run_loop(self):
        # 1. Inputs
        inputs = self.gui.get_inputs()
        adcs = self.esp32.read_adc()

        # Extract individual ADC values, with robust fallback to 0 if not available
        adc_raw = adcs[0] if isinstance(adcs, list) and len(adcs) > 0 else None
        adc_pv_raw = adcs[1] if isinstance(adcs, list) and len(adcs) > 1 else 0
        adc_grid_raw = adcs[2] if isinstance(adcs, list) and len(adcs) > 2 else 0

        # Extract Load PWM Feedback (Virtual ADCs)
        f_r = adcs[4] if isinstance(adcs, list) and len(adcs) > 4 else 0 # Pin 2
        f_g = adcs[5] if isinstance(adcs, list) and len(adcs) > 5 else 0 # Pin 5
        f_b = adcs[6] if isinstance(adcs, list) and len(adcs) > 6 else 0 # Pin 4

        # Necessitem una estimació del voltatge actual per al Brain
        # Fem servir l'últim valor conegut si adc_raw és None per evitar salts
        v_adc = (adc_raw / 4095.0 * 50.0) if adc_raw is not None else self.last_v
        self.last_v = v_adc # Store for next iteration if ADC fails

        # 2. Brain (Lògica i Escalat)
        # The Brain decides based on the *measured* voltage (v_adc)
        processed = self.brain.process(inputs, adc_raw, v_adc)

        # ESTAT DEL BUS: S'elimina la simulació dinàmica. El bus es defineix 
        # exclusivament per la lectura real de l'ADC (Pin 34).
        v_bus_real = v_adc
        # El SoC es calcula com un escalat directe del voltatge mesurat (0-50V -> 0-100%)
        soc_real = max(0.0, min(100.0, (v_bus_real / 50.0) * 100.0))

        # Actualització del temps d'execució
        self.elapsed_time_h += 0.05
        ts = processed['timestamp']
        self.gui.label_date.setText(f"Temps Real: {self.elapsed_time_h:.1f} h \n\nData: {ts[6:8]}/{ts[4:6]}/2023 {ts[9:11]}:00 h")

        # Balanç de corrents per a la visualització (KCL al Bus DC físic)
        v_denom = max(v_bus_real, 1.0)
        i_s = processed['p_solar'] / v_denom
        i_g = processed['p_grid'] / v_denom
        i_c = processed['p_cons'] / v_denom
        i_net = i_s + i_g - i_c # Corrent neta residual estimada cap al condensador

        # Estat enviat a la GUI per a LCDs i Gràfics
        hw_state = {'v_bus': v_bus_real, 'soc': soc_real, 'i_net': i_net}

        # Add raw ADC values to processed for GUI's hardware monitor
        # 'adc_raw' is already added by brain.process
        processed['adc_pv_raw'] = adc_pv_raw
        processed['adc_grid_raw'] = adc_grid_raw

        # Feedback for HW monitor (Pins 2, 5, 4)
        processed['hw_loads'] = {'r': f_r, 'g': f_g, 'b': f_b}

        # Hardware Mapping: DAC 26 is the Grid
        processed['dac_grid_val'] = processed['dac_grid']

        # 4. Outputs
        self.gui.update_view(processed, hw_state)
        # Enviem dades als pins físics de l'ESP32
        if adcs is not None: # Check if adcs list was successfully retrieved
            # Mapegem els sliders (0-100%) a valors PWM (0-255) per als LEDs (R=0, B=1, G=2)
            # Només enviem PWM si la càrrega està "servida" pel Brain (Shedding)
            pwm_r = int(inputs['cons_sliders'][0] * 2.55) if processed['served'][0] else 0
            pwm_b = int(inputs['cons_sliders'][1] * 2.55) if processed['served'][1] else 0
            pwm_g = int(inputs['cons_sliders'][2] * 2.55) if processed['served'][2] else 0

            # Seguretat Dummy Load: Si V > 45V, forcem el LED Verd al 100% (Safety Sink)
            if v_adc > 45.0:
                pwm_g = 255

            # Pin 25: Solar (DAC) | Pin 26: Grid (DAC) | Pin 27: Unused (sent as grid) | Càrregues: R, G, B
            self.esp32.send_data(processed['dac_pv'], processed['dac_grid'], processed['dac_grid'],
                                 pwm_r, pwm_g, pwm_b) # Added PWM for R, G, B loads

    def shutdown(self):
        self.esp32.close()
        sys.exit()

if __name__ == "__main__":
    launcher = MainApp()
    sys.exit(launcher.app.exec_())