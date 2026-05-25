import sys
import serial
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
import csv
from collections import deque
import random
import os

# Importem la interfície des de ui.py (basada en ui_v3.ui)
from ui import Ui_MainWindow

# ---------------- CONFIGURACIÓ SERIAL ----------------
try:
    ser = serial.Serial("COM4", 115200, timeout=0.05)
except Exception as e:
    print(f"Error port sèrie COM4: {e}. Mode simulat actiu.")
    ser = None

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # --- Variables de Simulació ---
        self.v_bus = 400.0  # Voltatge inicial (V)
        self.soc = 50.0     # Estat de càrrega inicial (%)
        self.cap_bus = 0.01 # Capacitat del condensador de bus (F)
        self.dt = 0.05      # Pas de temps (50ms)
        
        # --- Càrrega de dades d'irradiància ---
        self.solar_data = []
        try:
            csv_path = os.path.join(os.path.dirname(__file__), 'irradiancia.csv')
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    # Busquem línies que comencin amb data (2023...) o números
                    if row and row[0] and row[0][0].isdigit():
                        try:
                            # La columna 1 (segona) és G(i) - irradiància
                            self.solar_data.append(float(row[1]))
                        except: continue
        except Exception as e:
            print(f"Error llegint CSV: {e}. Generant dades simulades.")
            self.solar_data = [500 + 200*random.uniform(-1,1) for _ in range(500)]
        
        if not self.solar_data: self.solar_data = [500.0]
        self.solar_idx = 0

        # Històrics per als gràfics
        self.hist_vbus = deque(maxlen=200)
        self.hist_vbus_adc = deque(maxlen=200)
        self.hist_soc = deque(maxlen=200)
        self.hist_solar = deque(maxlen=200)
        self.hist_grid = deque(maxlen=200)
        self.hist_cons = deque(maxlen=200)
        self.hist_i_solar = deque(maxlen=200)
        self.hist_i_grid = deque(maxlen=200)
        self.hist_i_cons = deque(maxlen=200)
        self.hist_i_net = deque(maxlen=200)

        # --- Configuració de la Finestra de Gràfics (Mosaic 2x2 a pantalla completa) ---
        self.graph_win = pg.GraphicsLayoutWidget(title="SCADA Micro-xarxa: Simulació + Hardware")
        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        self.graph_win.setGeometry(screen)
        
        # (0,0): Voltatge
        self.p1 = self.graph_win.addPlot(title="Tensió del Bus (V)")
        self.p1.showGrid(x=True, y=True)
        self.p1.addLegend()
        self.curve_vbus = self.p1.plot(pen=pg.mkPen('y', width=2), name="Simulat")
        self.curve_vbus_adc = self.p1.plot(pen='m', name="Mesurat (ADC34)")
        
        # (0,1): SoC
        self.p2 = self.graph_win.addPlot(title="Estat de Càrrega SoC (%)")
        self.p2.showGrid(x=True, y=True)
        self.p2.setYRange(0, 100)
        self.curve_soc = self.p2.plot(pen='g')
        
        self.graph_win.nextRow()
        
        # (1,0): Potències
        self.p3 = self.graph_win.addPlot(title="Potències (W)")
        self.p3.showGrid(x=True, y=True)
        self.p3.addLegend()
        self.curve_solar = self.p3.plot(pen=pg.mkPen('orange', width=2), name='Solar')
        self.curve_grid = self.p3.plot(pen=pg.mkPen('cyan', width=2), name='Xarxa')
        self.curve_cons = self.p3.plot(pen=pg.mkPen('red', width=2), name='Consum')

        # (1,1): Corrents
        self.p4 = self.graph_win.addPlot(title="Corrent (A)")
        self.p4.showGrid(x=True, y=True)
        self.p4.addLegend()
        self.curve_i_solar = self.p4.plot(pen=pg.mkPen('orange', width=2), name='Solar (A)')
        self.curve_i_grid = self.p4.plot(pen=pg.mkPen('cyan', width=2), name='Xarxa (A)')
        self.curve_i_cons = self.p4.plot(pen=pg.mkPen('r', width=2), name='Consum (A)')
        self.curve_i_net = self.p4.plot(pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine), name='Net (KCL)')

        self.graph_win.show()

        # Activar Sliders si estaven desactivats a la UI
        self.verticalSlider_2.setEnabled(True)
        self.horizontalSlider_1.setEnabled(True)
        self.horizontalSlider_2.setEnabled(True)
        self.horizontalSlider_3.setEnabled(True)

        # --- Timer ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.step)
        self.timer.start(50)

        # Connectar botó EXIT (pushButton_3 a ui.py)
        self.pushButton_3.clicked.connect(self.closeAll)

    def step(self):
        # 1. Fonts de dades: Solar (CSV) i Xarxa (Slider)
        p_solar_w = self.solar_data[self.solar_idx]
        self.solar_idx = (self.solar_idx + 1) % len(self.solar_data)
        
        v_grid_cmd = self.verticalSlider_2.value() # 0-255

        # 2. Hardware: DACs (A=Solar, B=Grid) i lectura ADC34
        v_bus_real = self.v_bus  # Fallback
        if ser:
            try:
                # Enviar Solar a DAC Pin 25 (A)
                dac_pv = int(max(0, min(255, (p_solar_w / 1000) * 255)))
                ser.write(f"A{dac_pv}\n".encode())
                # Enviar Xarxa a DAC Pin 26 (B)
                ser.write(f"B{v_grid_cmd}\n".encode())
                
                while ser.in_waiting > 0:
                    line = ser.readline().decode().strip()
                
                if line:
                    parts = line.split()
                    if len(parts) == 3:
                        _, _, adc = map(int, parts)
                        # Escalat ADC34 (0-4095) a un valor de voltatge de bus (ex: 0-600V)
                        v_bus_real = (adc / 4095) * 600
            except Exception:
                pass

        # 3. Física de la simulació
        # Xarxa: 127 és el punt neutre (0W).
        p_grid_w = (v_grid_cmd - 127) * 20 
        
        # Consum: suma de lliscadors horitzontals (Càrregues 1, 2 i 3)
        p_cons_w = (self.horizontalSlider_1.value() +
                    self.horizontalSlider_2.value() +
                    self.horizontalSlider_3.value()) * 5 

        # Corrents
        i_solar = p_solar_w / self.v_bus
        i_grid = p_grid_w / self.v_bus
        i_cons = p_cons_w / self.v_bus 
        
        # Llei de corrents de Kirchhoff al condensador (Net)
        i_net = i_solar + i_grid - i_cons 
        
        # Actualitzem voltatge del bus
        self.v_bus += (i_net / self.cap_bus) * self.dt 
        
        # Actualitzem SoC (molt lentament)
        self.soc -= (p_cons_w / 100000)
        self.soc = max(0, min(100, self.soc))

        # 4. Actualització de dades i gràfics
        self.hist_vbus.append(self.v_bus) 
        self.hist_vbus_adc.append(v_bus_real)
        self.hist_soc.append(self.soc)
        self.hist_solar.append(p_solar_w)
        self.hist_grid.append(p_grid_w)
        self.hist_cons.append(p_cons_w)
        
        self.hist_i_solar.append(i_solar)
        self.hist_i_grid.append(i_grid)
        self.hist_i_cons.append(-i_cons) # Negatiu per visualitzar consum
        self.hist_i_net.append(-i_net)   # Net (hauria de tancar el cercle a 0)

        self.curve_vbus.setData(list(self.hist_vbus))
        self.curve_vbus_adc.setData(list(self.hist_vbus_adc))
        self.curve_soc.setData(list(self.hist_soc))
        self.curve_solar.setData(list(self.hist_solar))
        self.curve_grid.setData(list(self.hist_grid))
        self.curve_cons.setData(list(self.hist_cons))
        
        self.curve_i_solar.setData(list(self.hist_i_solar))
        self.curve_i_grid.setData(list(self.hist_i_grid))
        self.curve_i_cons.setData(list(self.hist_i_cons))
        self.curve_i_net.setData(list(self.hist_i_net))
        
        # Actualització de displays LCD de ui.py
        self.lcdNumber_8.display(int(self.v_bus))       # Tensió Bus
        self.lcdNumber_11.display(int(self.soc))      # SoC
        self.lcdNumber_6.display(int(p_solar_w))      # Solar W
        self.lcdNumber_7.display(int(p_grid_w))       # Xarxa W
        self.lcdNumber_10.display(int(p_cons_w))      # Consum Total
        self.lcdNumber_16.display(int(i_net * self.v_bus)) # Potència Cap

    def closeAll(self):
        if ser: ser.close()
        self.graph_win.close()
        self.close()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())