from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import serial
from collections import deque

from control_ui import Ui_MainWindow

# ---------------- SERIAL ----------------
ser = serial.Serial("COM4", 115200, timeout=0.1)

# ---------------- MAIN ----------------
class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # sliders → ESP32
        self.verticalSlider_1.valueChanged.connect(self.send_A)
        self.verticalSlider_2.valueChanged.connect(self.send_B)

        # graph
        self.graph = pg.GraphicsLayoutWidget()
        self.graph.show()

        self.plot = self.graph.addPlot(title="ADC34")
        self.curve = self.plot.plot()

        self.data = deque(maxlen=200)

        # timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

    # -------- send DAC 1 --------
    def send_A(self, v):
        ser.write(f"A{v}\n".encode())

    # -------- send DAC 2 --------
    def send_B(self, v):
        ser.write(f"B{v}\n".encode())

    # -------- read ESP32 --------
    def update(self):
        if ser.in_waiting:
            try:
                line = ser.readline().decode().strip()
                i1, i2, adc = map(int, line.split())

                # update graph
                self.data.append(adc)
                self.curve.setData(list(self.data))

                # optional LCDs (if exist in UI)
                self.lcdNumber_1.display(i1)
                self.lcdNumber_2.display(i2)
                self.lcdNumber_3.display(adc)

            except:
                pass

# ---------------- RUN ----------------
app = QtWidgets.QApplication([])
w = MainWindow()
w.show()
app.exec_()