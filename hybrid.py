import sys
from PyQt5 import QtWidgets, QtCore
from gui import GUI
from brain import Brain
from control_esp32 import ESP32Controller
from simulation import MicroGridSimulator

print("Iniciant aplicació en mode HÍBRID (Simulació + ESP32)...")
print("IMPORTANT: Connecta el Pin 26 al Pin 34 de l'ESP32 per tancar el bucle.")

class HybridApp:
    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        
        self.gui = GUI(show_hw=True)
        self.gui.setWindowTitle("SCADA HÍBRID - Micro-xarxa")
        self.gui.show()
        
        self.brain = Brain()
        self.esp32 = ESP32Controller()
        self.sim = MicroGridSimulator() # Utilitzem la física per generar el voltatge teòric

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.run_loop)
        self.timer.start(50)

        self.gui.pushButton_3.clicked.connect(self.shutdown)

    def run_loop(self):
        # 1. Llegir inputs de la GUI i ADC real (Pin 34)
        inputs = self.gui.get_inputs()
        adcs = self.esp32.read_adc() # Retorna [a34, a35, a32] o None
        
        adc_raw = adcs[0] if isinstance(adcs, list) else None
        adc_pv_raw = adcs[1] if isinstance(adcs, list) else 0
        adc_grid_raw = adcs[2] if isinstance(adcs, list) else 0

        v_adc = (adc_raw / 4095.0 * 50.0) if adc_raw is not None else self.sim.v_bus

        # 2. El Brain decideix basant-se en el voltatge LLEGIT
        processed = self.brain.process(inputs, adc_raw, v_adc)

        # 3. El simulador calcula la física teòrica segons les potències del Brain
        # (Això genera el senyal que enviarem al Pin 27)
        v_sim, soc, i_s, i_g, i_c, i_n = self.sim.update(
            processed['p_solar'], processed['p_grid'], processed['p_cons'], 0.05
        )

        # 4. Transposem el Voltatge Simulat (0-50V) a rang DAC/PWM (0-255)
        v_sim_scaled = int(max(0, min(255, (v_sim / 50.0) * 255)))
        processed['v_sim_scaled'] = v_sim_scaled

        processed['adc_pv_raw'] = adc_pv_raw
        processed['adc_grid_raw'] = adc_grid_raw

        # Corregim el bug del SoC: s'ha de calcular sobre la tensió LLEGIDA (ADC), no la teòrica
        soc_adc = max(0.0, min(100.0, (v_adc / 50.0) * 100.0))

        # 5. Lògica de Xarxa (PWM): Si p_grid > 0, considerem que està connectada
        # Podem enviar un valor proporcional o un binari (0 o 255)
        grid_pwm_val = int(max(0, min(255, processed['dac_grid'])))

        # 6. Outputs:
        # dac_pv (A) -> Pin 25
        # v_sim_scaled (B) -> Pin 26 (VBus)
        # grid_pwm_val (V) -> Pin 27 (Xarxa)
        self.gui.update_view(processed, {'v_bus': v_adc, 'soc': soc_adc, 'i_net': i_n})
        self.esp32.send_data(processed['dac_pv'], v_sim_scaled, grid_pwm_val)

    def shutdown(self):
        self.esp32.close()
        sys.exit()

if __name__ == "__main__":
    launcher = HybridApp()
    sys.exit(launcher.app.exec_())