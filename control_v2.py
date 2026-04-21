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

        self.diesel_base = 0
        self.diesel = 0

        self.storage = 0.0   # NEW


# =========================================================
# CONTROLLER
# =========================================================
class EnergyController:

    def compute(self, s):
        pv = s.pv if s.pv_on else 0
        diesel = s.diesel_base

        gen = pv + diesel

        load = s.load[:]  # [red, green, blue]

        served = [False, False, False]
        remaining = gen

        # --------------------------------------------------
        # STEP 1: NON-CRITICAL FIRST (green, blue)
        # they can fail naturally
        # --------------------------------------------------
        for i in (1, 2):
            if remaining >= load[i]:
                served[i] = True
                remaining -= load[i]

        # --------------------------------------------------
        # STEP 2: CRITICAL LOAD (red)
        # must be served if possible
        # diesel is adjusted ONLY here
        # --------------------------------------------------
        red = load[0]

        if remaining >= red:
            served[0] = True
            remaining -= red
        else:
            missing = red - remaining

            # diesel compensates ONLY for critical
            diesel += missing
            gen += missing

            served[0] = True
            remaining = 0

        # --------------------------------------------------
        # STEP 3: STORAGE (infinite battery) (New)
        # --------------------------------------------------

        total_load = sum(load[i] if served[i] else 0 for i in range(3))

        net = gen - total_load

        # charge or discharge
        if net >= 0:
            s.storage += net
            storage_discharge = 0
        else:
            needed = -net

            discharge = min(s.storage, needed)
            s.storage -= discharge
            storage_discharge = discharge

        return diesel, served, s.storage, storage_discharge


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

        self._setup_indicators()
        self.init_ui_state()

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
        self.verticalSlider_2.valueChanged.connect(self.set_diesel)

        self.pushButton_1.clicked.connect(self.toggle_pv)
        self.pushButton_3.clicked.connect(self.closeAll)

    # =====================================================
    # INDICATORS SETUP
    # =====================================================
    def _setup_indicators(self):

        leds = [self.checkBox, self.checkBox_2, self.checkBox_3,
        self.checkBox_7, self.checkBox_8, self.checkBox_9]
        for led in leds:
            led.setEnabled(False)
            led.setFocusPolicy(QtCore.Qt.NoFocus)
            led.setChecked(False)

    def update_indicators(self, served):
        self.checkBox.setChecked(served[0])
        self.checkBox_3.setChecked(served[1])
        self.checkBox_2.setChecked(served[2])
        self.checkBox_7.setChecked(served[0])
        self.checkBox_8.setChecked(served[1])
        self.checkBox_9.setChecked(served[2])

    def init_ui_state(self):
        # force model reset
        self.state.load = [0, 0, 0]

        self.state.pv = 0
        self.state.diesel = 0

        # sliders reset
        self.horizontalSlider_1.setValue(0)
        self.horizontalSlider_2.setValue(0)
        self.horizontalSlider_3.setValue(0)

        self.verticalSlider_1.setValue(0)
        self.verticalSlider_2.setValue(0)

        # checkboxes OFF
        self.checkBox.setChecked(False)
        self.checkBox_2.setChecked(False)
        self.checkBox_3.setChecked(False)
        self.checkBox_7.setChecked(False)
        self.checkBox_8.setChecked(False)
        self.checkBox_9.setChecked(False)

    # =====================================================
    # SIMULATION LOOP
    # =====================================================
    def step(self):

        diesel, served = self.controller.compute(self.state)
        self.state.diesel = diesel

        effective_load = [
            self.state.load[i] if served[i] else 0
            for i in range(3)
        ]

        pv = self.state.pv if self.state.pv_on else 0
        gen = pv + diesel

        load = sum(effective_load)

        balance = gen - load

        # ---------------- UI ----------------
        self.lcdNumber_8.display(balance)
        self.lcdNumber_7.display(diesel)
        self.lcdNumber_9.display(gen)
        self.lcdNumber_10.display(load)

        self.lcdNumber_1.display(effective_load[0]) 
        self.lcdNumber_2.display(effective_load[1])
        self.lcdNumber_3.display(effective_load[2])

        self.lcdNumber_6.display(pv)

        # ---------------- GRAPH ----------------
        self.history.append(balance)
        self.curve.setData(list(self.history))

        # ---------------- INDICATORS ----------------
        self.update_indicators(served)

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
        self.lcdNumber_time.display(self.simulation_time)
        self.label_time.setText(f"Time: {self.simulation_time:.1f} s")

    # =====================================================
    # INPUT HANDLERS
    # =====================================================
    def set_load(self, i, value):
        self.state.load[i] = value

    def set_pv(self, value):
        self.state.pv = value

    def set_diesel(self, value):
        self.state.diesel_base = value

    # solar toggle WITH SLIDER RESET
    def toggle_pv(self):
        self.state.pv_on = not self.state.pv_on

        if not self.state.pv_on:
            self.state.pv = 0
            self.verticalSlider_1.blockSignals(True)
            self.verticalSlider_1.setValue(0)
            self.verticalSlider_1.setEnabled(False)
            self.verticalSlider_1.blockSignals(False)
        else:
            self.verticalSlider_1.setEnabled(True)

    # =====================================================
    # CLOSE BOTH WINDOWS
    # =====================================================
    def closeAll(self):
        self.graph_win.close()
        self.close()


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())