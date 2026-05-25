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
        self.gui = GUI(show_hw=True)
        self.gui.show()
        self.brain = Brain()
        self.esp32 = ESP32Controller()

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
        adc_raw = adcs[0] if isinstance(adcs, list) else adcs
        
        # Necessitem una estimació del voltatge actual per al Brain
        # Fem servir l'últim valor conegut si adc_raw és None per evitar salts
        v_current = (adc_raw / 4095.0 * 50.0) if adc_raw is not None else getattr(self, 'last_v', 40.0)
        self.last_v = v_current

        # 2. Brain (Lògica i Escalat)
        processed = self.brain.process(inputs, adc_raw, v_current)

        # 3. Càlcul de l'estat Real (Sense simulador)
        v_real = processed['v_bus_real']
        v_safe = max(v_real, 5.0) # Evitar div per zero (mínim 5V per a càlculs d'intensitat)
        
        # Calculem corrents reals per a la gràfica
        i_s = processed['p_solar'] / v_safe 
        i_g = processed['p_grid'] / v_safe
        i_c = processed['p_cons'] / v_safe
        i_n = i_s + i_g - i_c

        # SoC mapejat: 0V (0%) a 50V (100%)
        soc_real = max(0.0, min(100.0, (v_real / 50.0) * 100.0))
        hw_state = {'v_bus': v_real, 'soc': soc_real, 'i_net': i_n}

        # 4. Outputs
        self.gui.update_view(processed, hw_state)
        # Enviem dades als pins físics de l'ESP32
        if adc_raw is not None:
            self.esp32.send_data(processed['dac_pv'], processed['dac_grid'])

    def shutdown(self):
        self.esp32.close()
        sys.exit()

if __name__ == "__main__":
    launcher = MainApp()
    sys.exit(launcher.app.exec_())