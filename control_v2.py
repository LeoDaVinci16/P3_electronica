# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
from collections import deque

from ui_v2 import Ui_MainWindow


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
        gen = pv + grid

        load = sum(effective_load)

        balance = gen - load

        # ---------------- UI ----------------
        self.lcdNumber_8.display(balance)
        self.lcdNumber_7.display(grid)
        self.lcdNumber_9.display(gen)
        self.lcdNumber_10.display(load)

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