# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtWidgets
import pyqtgraph as pg
from PyQt5.QtCore import QTimer
from ui_v2 import *


# -------------------------------
# MODEL
# -------------------------------
class EnergySystem:
    def __init__(self):
        self.carga = [0, 0, 0]          # requested loads
        self.carga_on = [True, True, True]  # actual delivered loads

        self.pv = 0
        self.pv_on = True

        self.diesel = 0
        self.diesel_base = 0
        self.generador_on = True


# -------------------------------
# CONTROLLER
# -------------------------------
class DieselController:
    def update(self, system: EnergySystem):

        pv = system.pv if system.pv_on else 0

        red_demand = system.carga[0]

        # ----------------------------
        # CRITICAL LOGIC (RED ONLY)
        # ----------------------------

        if pv >= red_demand:
            # PV alone is enough → no diesel needed
            system.carga_on[0] = True
            system.diesel = 0

        else:
            # PV not enough → diesel covers the gap
            missing = red_demand - pv
            system.diesel = missing
            system.carga_on[0] = True

        # ----------------------------
        # NON-CRITICAL LOADS (BLUE/GREEN)
        # only use surplus energy
        # ----------------------------

        available = max(0, pv + system.diesel - red_demand)

        # BLUE (index 1)
        if available >= system.carga[1]:
            system.carga_on[1] = True
            available -= system.carga[1]
        else:
            system.carga_on[1] = False

        # GREEN (index 2)
        if available >= system.carga[2]:
            system.carga_on[2] = True
            available -= system.carga[2]
        else:
            system.carga_on[2] = False


# -------------------------------
# MAIN WINDOW
# -------------------------------
class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()

        self.system = EnergySystem()
        self.controller = DieselController()

        self.setupUi(self)

        # ---------------- TIMER ----------------
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateSystem)
        self.timer.start(100)

        # ---------------- BUTTONS ----------------
        self.pushButton_1.clicked.connect(self.toggleSolar)
        self.pushButton_2.clicked.connect(self.toggleDiesel)
        self.pushButton_3.clicked.connect(self.closeAll)

        # ---------------- SLIDERS ----------------
        self.horizontalSlider_1.valueChanged.connect(lambda v: self.setCarga(0, v))
        self.horizontalSlider_2.valueChanged.connect(lambda v: self.setCarga(1, v))
        self.horizontalSlider_3.valueChanged.connect(lambda v: self.setCarga(2, v))

        self.verticalSlider_1.valueChanged.connect(self.setPV)
        self.verticalSlider_2.valueChanged.connect(self.setDiesel)

    # ---------------- SYSTEM LOOP ----------------
    def updateSystem(self):

        global curva, dataN, dataY, lastN, win

        self.controller.update(self.system)

        gen = (self.system.pv if self.system.pv_on else 0) + self.system.diesel
        load = sum(
            self.system.carga[i] if self.system.carga_on[i] else 0
            for i in range(3)
        )
        balance = gen - load

        # ---------------- LCDS ----------------
        self.lcdNumber_8.display(balance)
        self.lcdNumber_7.display(self.system.diesel)
        self.lcdNumber_9.display(gen)
        self.lcdNumber_10.display(load)

        # ---------------- UPDATE LOAD DISPLAY (REAL OUTPUT) ----------------
        self.refreshLoads()

        # ---------------- BUTTON TEXT ----------------
        self.pushButton_1.setText("Solar ON" if self.system.pv_on else "Solar OFF")
        self.pushButton_2.setText("Diesel ON" if self.system.generador_on else "Diesel OFF")

        # ---------------- GRAPH ----------------
        dataY.append(balance)
        dataN.append(lastN)
        lastN += 1

        if len(dataN) > 200:
            dataN = dataN[-200:]
            dataY = dataY[-200:]

        curva.setData(dataN, dataY)

    # ---------------- LOAD DISPLAY ----------------
    def refreshLoads(self):
        self.lcdNumber_1.display(self.system.carga[0] if self.system.carga_on[0] else 0)
        self.lcdNumber_2.display(self.system.carga[1] if self.system.carga_on[1] else 0)
        self.lcdNumber_3.display(self.system.carga[2] if self.system.carga_on[2] else 0)

    # ---------------- INPUTS ----------------
    def setCarga(self, i, value):
        self.system.carga[i] = value
        if value > 0:
            self.system.carga_on[i] = True

    def setPV(self, value):
        if self.system.pv_on:
            self.system.pv = value
        else:
            self.system.pv = 0
        self.lcdNumber_6.display(self.system.pv)

    def setDiesel(self, value):
        self.system.diesel_base = value
        self.lcdNumber_7.display(value)

    # ---------------- BUTTONS ----------------
    def toggleSolar(self):
        self.system.pv_on = not self.system.pv_on
        if not self.system.pv_on:
            self.system.pv = 0
        self.lcdNumber_6.display(self.system.pv)

    def toggleDiesel(self):
        self.system.generador_on = not self.system.generador_on
        if not self.system.generador_on:
            self.system.diesel = 0

    # ---------------- CLOSE ALL ----------------
    def closeAll(self):
        global win
        try:
            win.close()
        except:
            pass
        self.close()


# -------------------------------
# GRAPH
# -------------------------------
app = QtWidgets.QApplication.instance()
if app is None:
    app = QtWidgets.QApplication([])

win = pg.GraphicsLayoutWidget(title="Balanç Energètic")
win.show()

p = win.addPlot(title="Balance")
curva = p.plot(pen='y')
p.enableAutoRange(axis='y')

dataN = []
dataY = []
lastN = 0


# -------------------------------
# MAIN
# -------------------------------
if __name__ == "__main__":
    window = MainWindow()
    window.show()
    app.exec_()