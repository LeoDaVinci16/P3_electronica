from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import serial
from collections import deque
import sys

# Importem la teva interfície generada
from control_ui import Ui_MainWindow

# ---------------- CONFIGURACIÓ SERIAL ----------------
try:
    ser = serial.Serial("COM4", 115200, timeout=0.1)
except Exception as e:
    print(f"Error obrint el port sèrie: {e}")
    sys.exit()

# ---------------- CLASSE PRINCIPAL ----------------
class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Connectar Sliders
        self.verticalSlider_1.valueChanged.connect(self.send_A)
        self.verticalSlider_2.valueChanged.connect(self.send_B)

        # Configurar Gràfica (PyQtGraph)
        self.graph_layout = pg.GraphicsLayoutWidget()
        # Busquem on posar la gràfica a la teva UI. 
        # Si no tens un layout definit, la mostrem en una finestra nova:
        self.graph_layout.show()
        self.plot = self.graph_layout.addPlot(title="Lectura ADC Pin 34")
        self.curve = self.plot.plot(pen='y') # Línia groga

        self.data = deque(maxlen=200)
        # Timer per actualitzar la interfície cada 50ms
        self.timer = QtCore.QTimer()    
        self.timer.timeout.connect(self.update_logic)
        self.timer.start(50)

    def send_A(self, v):
        ser.write(f"A{v}\n".encode())

    def send_B(self, v):
        ser.write(f"B{v}\n".encode())

    def update_logic(self):
        # Read all available lines to get the most recent one and clear the buffer
        line = None
        while ser.in_waiting > 0:
            line = ser.readline().decode().strip()

        if line:
            try:
                # Separem els 3 valors que envia l'ESP32
                parts = line.split()
                if len(parts) == 3:
                    i1, i2, adc = map(int, parts)

                    # 1. MOSTRAR PER TERMINAL (el que demanaves)
                    print(f"DAC25: {i1} | DAC26: {i2} | ADC34: {adc}")
                    self.lcdNumber_6.display(i1)
                    self.lcdNumber_7.display(i2)
                    self.lcdNumber_8.display(adc)

                    # 2. Actualitzar gràfica
                    self.data.append(adc)
                    self.curve.setData(list(self.data))

                    # 3. Actualitzar LCDs (si existeixen a la UI)
                    if hasattr(self, 'lcdNumber_1'): self.lcdNumber_1.display(i1)
                    if hasattr(self, 'lcdNumber_2'): self.lcdNumber_2.display(i2)
                    if hasattr(self, 'lcdNumber_3'): self.lcdNumber_3.display(adc)
            except Exception:
                pass

    def closeEvent(self, event):
        """Es tanca quan tanques la finestra"""
        ser.close()
        self.graph_layout.close()
        event.accept()

# ---------------- EXECUCIÓ ----------------
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())