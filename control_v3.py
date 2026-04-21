# -*- coding: utf-8 -*-
import pandas as pd
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
from collections import deque

from ui_v3 import Ui_MainWindow


# =========================================================
# MODEL
# =========================================================
class EnergyState:
    def __init__(self):
        self.load = [0, 0, 0]
        self.load_enabled = [True, True, True]

        self.pv = 0
        self.pv_on = True

        self.grid_base = 0
        self.grid = 0

        self.storage = 0.0


# =========================================================
# CONTROLLER
# =========================================================
class EnergyController:

    def compute(self, s):
        pv = s.pv if s.pv_on else 0
        grid = s.grid_base

        gen = pv + grid

        load = s.load[:]  # [red, green, blue]

        served = [False, False, False]
        remaining = gen

        # --------------------------------------------------
        # STEP 1: CRITICAL LOAD (red)
        # must be served if possible
        # grid is adjusted ONLY here
        # --------------------------------------------------
        red = load[0]

        if remaining >= red:
            served[0] = True
            remaining -= red
        else:
            missing = red - remaining

            # grid compensates ONLY for critical
            grid += missing
            gen += missing

            served[0] = True
            remaining = 0

        # --------------------------------------------------
        # STEP 2: NON-CRITICAL FIRST (green, blue)
        # they can fail naturally
        # --------------------------------------------------
        for i in (1, 2):
            if remaining >= load[i]:
                served[i] = True
                remaining -= load[i]

        return grid, served


# =========================================================
# MAIN WINDOW
# =========================================================
class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        # ----------------- SIMULATION TIME --------------------------
        self.simulation_time = 0.0
        self.dt = 0.1

        self.setupUi(self)

        self.state = EnergyState()
        self.controller = EnergyController()

        self.history = deque(maxlen=200)

        QtCore.QTimer.singleShot(0, self.step)

        # ------------ DADES DE SOLAR ----------------
        self.V_bus = 10.0          # Tensió inicial (V)
        self.V_ref = 10.0          # Referència de 10V
        self.C = 5.0               # Capacitat ajustada per a corrents de max 25.5A
        self.dt = 0.02             # Pas de temps (20ms)
        self.escala_I = 0.1        # Factor de conversió: Slider 255 -> 25.5 Amperis
        try:
            nom_fitxer = 'Timeseries_41.394_2.165_SA3_39deg_0deg_2023_2023.csv'

            df = pd.read_csv(nom_fitxer, skiprows=8, skipfooter=10, engine='python')
            df['time'] = pd.to_datetime(df['time'], format='%Y%m%d:%H%M')
            
            # Filtre de setmana (168 hores)
            df_setmana = df.iloc[0:168] 
            
            self.dades_irradiancia = df_setmana['G(i)'].values
            self.dades_temps = df_setmana['time'].dt.strftime('%Y%m%d:%H%M').values
            self.total_hores = len(self.dades_irradiancia)
            print(f"✅ Simulació 10V / 25A preparada: {self.total_hores} hores.")
        except Exception as e:
            print(f"❌ Error dades: {e}")
            self.dades_irradiancia = [0]*168
            self.dades_temps = ["00000000:0000"]*168

        self.index_hora = 0 
        self.corrent_pv = 0
        self.corrent_xarxa = 0
        self.carga_1 = self.carga_2 = self.carga_3 = 0
        self.xarxa_conectada = False

        # ---------------- GRAPH WINDOW ----------------
        self.graph_win = pg.GraphicsLayoutWidget(title="Balanç Energètic")
        self.graph_win.resize(800, 400)

        self.plot = self.graph_win.addPlot(title="Balance")
        self.curve = self.plot.plot()

        self.graph_win.show()

        # ---------------- TIMER ----------------
        self.timer = QTimer()
        self.timer.timeout.connect(self.step)
        self.timer.start(100)

        # ---------------- INPUTS ----------------
        self.horizontalSlider_1.valueChanged.connect(lambda v: self.set_load(0, v))
        self.horizontalSlider_2.valueChanged.connect(lambda v: self.set_load(1, v))
        self.horizontalSlider_3.valueChanged.connect(lambda v: self.set_load(2, v))

        self.verticalSlider_1.valueChanged.connect(self.set_pv)
        self.verticalSlider_2.valueChanged.connect(self.set_grid)

        self.pushButton_1.clicked.connect(self.toggle_pv)
        self.pushButton_3.clicked.connect(self.closeAll)

    # ----------------------- LED INDICATORS --------------
        self.state.load = [0, 0, 0]
        self.state.pv = 0
        self.state.grid = 0

        self.horizontalSlider_1.setValue(0)
        self.horizontalSlider_2.setValue(0)
        self.horizontalSlider_3.setValue(0)

        self.verticalSlider_1.setValue(0)
        self.verticalSlider_2.setValue(0)

    # =====================================================
    # SIMULATION LOOP
    # =====================================================
    def step(self):
        grid, served = self.controller.compute(self.state)
        self.state.grid = grid

        effective_load = [
            self.state.load[i] if served[i] else 0
            for i in range(3)
        ]

        pv = self.state.pv if self.state.pv_on else 0

        # 1. Entrada PV Escalada (0 a 25.5 A)
        irr = self.dades_irradiancia[self.index_hora]
        self.corrent_pv = (irr / 1000) * 255 * self.escala_I
        
        ts = self.dades_temps[self.index_hora]
        self.label.setText(f"Simulació 10V | {ts[6:8]}/{ts[4:6]} {ts[9:11]}:00")
        
        # 2. Control de Xarxa (Suport a Càrrega 1)
        if self.V_bus < self.V_ref:
            if not self.xarxa_conectada: self.botonON()
            
            error = self.V_ref - self.V_bus
            # Guany de control per ajustar el corrent (en Amperis reals)
            i_suport = error * 15.0 
            
            # Convertim els Amperis de tornada a valor de Slider (0-255) per visualització
            val_slider = i_suport / self.escala_I
            self.verticalSlider_2.setValue(int(min(255, max(0, val_slider))))
            
            self.corrent_xarxa = min(25.5, max(0, i_suport))

        # 3. Dinàmica del Bus (KCL)
        # Apliquem l'escala a les càrregues dels sliders
        i_cons_total = (self.carga_1 + self.carga_2 + self.carga_3) * self.escala_I
        i_gen_total = self.corrent_pv + (self.corrent_xarxa if self.xarxa_conectada else 0)
        
        i_net = i_gen_total - i_cons_total
        
        # dV = (I_net / C) * dt
        self.V_bus += (i_net / self.C) * self.dt
        
        # Límits de seguretat
        self.V_bus = max(0, min(self.V_bus, 15.0)) 

        # 4. LCDs (Amb el valor real de corrent per a la generació i consum)
        self.lcdNumber_8.display(float(f"{self.V_bus:.2f}"))
        self.lcdNumber_9.display(float(f"{i_gen_total:.1f}"))
        self.lcdNumber_10.display(float(f"{i_cons_total:.1f}"))

        gen = pv + grid # i_cons_total

        load = sum(effective_load) # i_gen_total

        balance = gen - load # i_net

        # ---------------- UI ----------------
        #self.lcdNumber_8.display(balance)
        self.lcdNumber_7.display(grid)
        #self.lcdNumber_9.display(gen)
        #self.lcdNumber_10.display(load)

        self.lcdNumber_1.display(effective_load[0]) 
        self.lcdNumber_2.display(effective_load[1])
        self.lcdNumber_3.display(effective_load[2])

        self.checkBox.setChecked(self.state.load[0] > 0)
        self.checkBox_3.setChecked(self.state.load[1] > 0)
        self.checkBox_2.setChecked(self.state.load[2] > 0)

        self.checkBox_7.setChecked(self.state.load[0] > 0)
        self.checkBox_8.setChecked(self.state.load[1] > 0)
        self.checkBox_9.setChecked(self.state.load[2] > 0)

        self.lcdNumber_6.display(pv)

        # ---------------- GRAPH ----------------
        self.history.append(balance)
        self.curve.setData(list(self.history))

        # ------------- set led slider to 0 if it breaks ----------------
        sliders = [
            self.horizontalSlider_1,
            self.horizontalSlider_2,
            self.horizontalSlider_3
        ]

        for i in (1, 2):
            if not served[i] and sliders[i].value() != 0:
                sliders[i].setValue(0)

        # time:
        self.simulation_time += self.dt
        self.label_time.setText(f"Time: {self.simulation_time:.1f} s")

    # =====================================================
    # INPUT HANDLERS
    # =====================================================
    def set_load(self, i, value):
        self.state.load[i] = value
        print(f"Càrrega led val {value}")

    def set_pv(self, value):
        self.state.pv = value
        print(f"Solar val: {value}")

    def set_grid(self, value):
        self.state.grid_base = value
        print(f"La xarxa val: {value}")

    # solar toggle WITH SLIDER RESET
    def toggle_pv(self):
        self.state.pv_on = not self.state.pv_on

        if not self.state.pv_on:
            self.state.pv = 0
            self.verticalSlider_1.blockSignals(True)
            self.verticalSlider_1.setValue(0)
            self.verticalSlider_1.setEnabled(False)
            self.verticalSlider_1.blockSignals(False)
            print("S'ha desconectat la FV")
        else:
            self.verticalSlider_1.setEnabled(True)
            print("S'ha connectat la FV")

    # =====================================================
    # CLOSE BOTH WINDOWS
    # =====================================================
    def closeAll(self):
        self.graph_win.close()
        self.close()
        print("S'ha apagat la aplicació")


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())