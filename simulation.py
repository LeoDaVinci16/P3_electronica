
import sys
from PyQt5 import QtWidgets, QtCore
from gui import GUI
from brain import Brain

class StandaloneSim:
    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.gui = GUI(show_hw=False)
        self.gui.setWindowTitle("SIMULADOR Micro-xarxa (Sense Hardware)")
        self.gui.show()
        
        self.brain = Brain()
        self.sim = MicroGridSimulator()
        self.sim_time_h = 0.0

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.loop)
        self.timer.start(50)
        
        self.gui.pushButton_3.clicked.connect(sys.exit)

    def loop(self):
        # Inputs de la GUI
        inputs = self.gui.get_inputs()
        
        # Brain processa fent servir el voltatge simulat actual
        processed = self.brain.process(inputs, None, self.sim.v_bus)
        
        # Actualització del temps i el label
        self.sim_time_h += 0.05
        ts = processed['timestamp']
        self.gui.label_date.setText(f"Durada total: {self.sim_time_h:.1f} h \n\nData: {ts[6:8]}/{ts[4:6]}/2023 {ts[9:11]}:00 h")

        # Física del simulador
        v, soc, i_s, i_g, i_c, i_n = self.sim.update(
            processed['p_solar'], processed['p_grid'], processed['p_cons'], 0.05
        )
        
        sim_res = {'v_bus': v, 'soc': soc, 'i_net': i_n}
        
        # Actualitzem GUI
        self.gui.update_view(processed, sim_res)

class MicroGridSimulator:
    def __init__(self, v_bus_init=40.0, soc_init=100.0, cap=12.0):
        self.v_bus = v_bus_init
        self.soc = soc_init
        self.cap_bus = cap

    def update(self, p_solar, p_grid, p_cons, dt):
        # Evitem divisió per zero
        v_current = max(self.v_bus, 10.0)
        
        # Càlcul de corrents (I = P/V)
        i_solar = p_solar / v_current
        i_grid = p_grid / v_current
        i_cons = p_cons / v_current
        
        # Simulem una petita autodescàrrega o pèrdues internes (Resistència en paral·lel)
        # Això fa que la càrrega sigui asimptòtica (exponencial) i no purament lineal.
        i_loss = self.v_bus / 200.0  # Equivalent a una R de pèrdues de 200 ohms

        # Llei de corrents de Kirchhoff (KCL)
        i_net = i_solar + i_grid - i_cons - i_loss
        
        # Actualització de voltatge: dv = (i/C)*dt
        self.v_bus += (i_net / self.cap_bus) * dt
        # Clamping de seguretat
        self.v_bus = max(10.0, min(50.0, self.v_bus))
        
        # SoC mapejat: 0V (0%) a 50V (100%)
        self.soc = max(0.0, min(100.0, (self.v_bus / 50.0) * 100.0))
        print(f"Sim: V={self.v_bus:.2f}V | SoC={self.soc:.1f}% | I_net={i_net:.2f}A")
        return self.v_bus, self.soc, i_solar, i_grid, i_cons, i_net

if __name__ == "__main__":
    print("Iniciant simulació independent...")
    sim_app = StandaloneSim()
    sys.exit(sim_app.app.exec_())