from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
from collections import deque
from ui import Ui_MainWindow

class GUI(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, show_hw=False, mode='hybrid'):
        super().__init__()
        self.show_hw = show_hw
        self.mode = mode
        self.setupUi(self)

        # Actualitzem etiquetes per reflectir percentatge (%) en lloc d'Amperis
        self.label_5.setText("CONSUM (%):") # Already updated in previous step
        self.label_22.setText("%") # Change "Ampers" to "%" in schematic

        # Configuració de tots els LCDs per mostrar fins a 5 dígits
        lcds = [self.lcdNumber_1, self.lcdNumber_2, self.lcdNumber_3, self.lcdNumber_6, 
                self.lcdNumber_7, self.lcdNumber_8, self.lcdNumber_9, self.lcdNumber_10, 
                self.lcdNumber_11, self.lcdNumber_12, self.lcdNumber_13, self.lcdNumber_14, 
                self.lcdNumber_15, self.lcdNumber_16, self.lcdNumber, self.lcdNumber_4, self.lcdNumber_5]
        for lcd in lcds:
            lcd.setDigitCount(5)

        # Colors per als indicadors de consum
        self._set_lcd_color(self.lcdNumber_1, "red")
        self._set_lcd_color(self.lcdNumber_2, "blue")
        self._set_lcd_color(self.lcdNumber_3, "green")

        # Configure Grid Slider as percentage (0-100)
        self.verticalSlider_2.setRange(0, 100)
        self.verticalSlider_2.setEnabled(True)

        self._setup_plots()
        self._enable_controls()
        if self.show_hw:
            self._setup_hw_monitor()
        self.pushButton_3.clicked.connect(self.close_all)

    def _set_lcd_color(self, lcd, color):
        pal = lcd.palette()
        pal.setColor(QtGui.QPalette.WindowText, QtGui.QColor(color))
        lcd.setPalette(pal)
        lcd.setSegmentStyle(QtWidgets.QLCDNumber.Flat)

    def _setup_plots(self):
        self.graph_win = pg.GraphicsLayoutWidget(title="Monitorització Micro-xarxa")
        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        self.graph_win.setGeometry(screen)
        
        self.p1 = self.graph_win.addPlot(title="Tensió del Bus")
        self.p1.setLabel('left', "Voltatge", units='V')
        self.p1.addLegend()
        self.curve_vbus = self.p1.plot(pen=pg.mkPen('y', width=2), name="Bus")
        
        self.p2 = self.graph_win.addPlot(title="Estat de Càrrega")
        self.p2.setLabel('left', "SoC", units='%')
        self.p2.setYRange(0, 100)
        self.curve_soc = self.p2.plot(pen='g', name="SoC")
        
        self.graph_win.nextRow()
        
        self.p3 = self.graph_win.addPlot(title="Balanç de Potències (W)")
        self.p3.setLabel('left', "Potència", units='W')
        self.p3.addLegend()
        self.curve_p_sol = self.p3.plot(pen=pg.mkPen('orange', width=2), name='Solar')
        self.curve_p_grid = self.p3.plot(pen=pg.mkPen('cyan', width=2), name='Xarxa')
        self.curve_p_cons = self.p3.plot(pen=pg.mkPen('red', width=2), name='Consum')
        self.curve_p_cap = self.p3.plot(pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine), name='Capacitat')
        
        # Update plot for load duty cycles
        self.p4 = self.graph_win.addPlot(title="Duty Cycle Càrregues (%)")
        self.p4.setLabel('left', "Duty Cycle", units='%')
        self.p4.addLegend()
        self.curve_i_sol = self.p4.plot(pen=pg.mkPen('orange', width=1), name='Solar (mA)')
        self.curve_i_grid = self.p4.plot(pen=pg.mkPen('cyan', width=1), name='Xarxa (mA)')
        self.curve_i_cons = self.p4.plot(pen=pg.mkPen('red', width=1), name='Càrrega 1 (%)') # Changed to %
        self.curve_i_load2 = self.p4.plot(pen=pg.mkPen('blue', width=1), name='Càrrega 2 (%)') # New curve for load 2
        self.curve_i_load3 = self.p4.plot(pen=pg.mkPen('green', width=1), name='Càrrega 3 (%)') # New curve for load 3
        self.curve_i_net = self.p4.plot(pen=pg.mkPen('w', style=QtCore.Qt.DashLine), name='I Net (Cap)')
        
        self.graph_win.show()
        
        self.h = {k: deque(maxlen=200) for k in ['vs','vr','soc','ps','pg','pc','in', 'is', 'ig', 'ic', 'il2', 'il3', 'pcp']}

    def _setup_hw_monitor(self):
        # Finestra per a senyals de baix nivell (Pins ESP32)
        self.hw_win = pg.GraphicsLayoutWidget(title="Monitorització de l'ESP32")
        self.hw_win.resize(500, 1000)

        # Plot 1: Solar System (DAC 25 & ADC 35)
        self.p_solar_hw = self.hw_win.addPlot(title="Solar: Pin 25 (DAC) vs Pin 35 (ADC)")
        self.p_solar_hw.setYRange(0, 3.3)
        self.p_solar_hw.addLegend()
        self.curve_d25 = self.p_solar_hw.plot(pen='orange', name="DAC 25")
        self.curve_a35 = self.p_solar_hw.plot(pen='m', name="ADC 35")

        self.hw_win.nextRow()

        # Plot 2: Grid System (DAC 26 & ADC 32)
        title_26 = "Grid: Pin 26 (DAC) vs Pin 32 (ADC)"
        self.p_grid_hw = self.hw_win.addPlot(title=title_26)
        self.p_grid_hw.setYRange(0, 3.3)
        self.p_grid_hw.addLegend()
        self.curve_d26 = self.p_grid_hw.plot(pen='cyan', name="DAC 26")
        self.curve_a32 = self.p_grid_hw.plot(pen='m', name="ADC 32")

        self.hw_win.nextRow()

        # Plot 3: DC Bus (ADC 34)
        self.p_bus_hw = self.hw_win.addPlot(title="DC Bus: Pin 34 (ADC)")
        self.p_bus_hw.setYRange(0, 3.3)
        self.p_bus_hw.addLegend()
        self.curve_a34 = self.p_bus_hw.plot(pen='y', name="ADC 34")

        self.hw_win.nextRow()

        # Plot 4: Loads PWM Effective Voltage (Pins 2, 5, 4)
        self.p_loads_hw = self.hw_win.addPlot(title="Loads PWM (Effective V): Pins 2, 5, 4")
        self.p_loads_hw.setYRange(0, 3.3)
        self.p_loads_hw.addLegend()
        self.curve_p2 = self.p_loads_hw.plot(pen='red', name="Pin 2 (R)")
        self.curve_p5 = self.p_loads_hw.plot(pen='green', name="Pin 5 (G)")
        self.curve_p4 = self.p_loads_hw.plot(pen='blue', name="Pin 4 (B)")

        self.hw_win.show()
        # History buffers for low-level signals
        self.hw_h = {k: deque(maxlen=200) for k in [
            'd25', 'a35', # Solar
            'd26', 'a32', # Grid
            'a34',        # Bus
            'p2', 'p5', 'p4' # Loads
        ]}

    def _enable_controls(self):
        self.verticalSlider_2.setEnabled(True)
        self.horizontalSlider_1.setEnabled(True)
        self.horizontalSlider_2.setEnabled(True)
        self.horizontalSlider_3.setEnabled(True)

    def get_inputs(self):
        return {
            'grid_slider': self.verticalSlider_2.value(),
            'cons_sliders': [self.horizontalSlider_1.value(), 
                             self.horizontalSlider_2.value(), 
                             self.horizontalSlider_3.value()]
        }

    def update_view(self, data, sim_state):
        # Lògica de Reset de Sliders (Shedding)
        if not data['served'][1] and self.horizontalSlider_2.value() > 0:
            self.horizontalSlider_2.setValue(0)
        if not data['served'][2] and self.horizontalSlider_3.value() > 0:
            self.horizontalSlider_3.setValue(0)

        # Reset lliscador xarxa si el Brain ha forçat la desconnexió (>35V)
        if data.get('grid_forced_off') and self.verticalSlider_2.value() > 0:
            self.verticalSlider_2.setValue(0)

        v = sim_state['v_bus']
        soc = sim_state['soc']
        i_net = sim_state['i_net']
        p_solar = data['p_solar']
        p_grid = data['p_grid']
        p_cons = data['p_cons']
        p_cap = i_net * v

        # Càlcul de corrents individuals per als LCDs (Power / Voltage)
        # Les càrregues ara representen el Duty Cycle (%) enviat als LEDs
        inputs = self.get_inputs()
        i_loads = [inputs['cons_sliders'][i] if data['served'][i] else 0.0 for i in range(3)]

        # Seguretat Dummy Load: Si V > 45V, el LED Verd (index 2) està al 100%
        if v > 45.0:
            i_loads[2] = 100.0

        # 1. Secció de Potències (W) - No changes here
        self.lcdNumber_6.display(int(p_solar))
        self.lcdNumber_7.display(int(p_grid))
        self.lcdNumber_9.display(int(p_solar + p_grid)) # Potència Disponible
        self.lcdNumber_10.display(int(p_cons))
        self.lcdNumber_16.display(int(p_cap))           # Potència Condensador

        # 2. Secció d'Estat (V / %)
        self.lcdNumber_8.display(float(f"{v:.2f}"))
        self.lcdNumber_11.display(int(soc))

        # 3. Duty Cycle Càrrega (%)
        self.lcdNumber_1.display(float(f"{i_loads[0]:.1f}"))
        self.lcdNumber_2.display(float(f"{i_loads[1]:.1f}"))
        self.lcdNumber_3.display(float(f"{i_loads[2]:.1f}"))

        # 4. Esquema (Corrents A, Voltatge V i Duty Cycle %)
        self.lcdNumber.display(float(f"{p_solar/max(v,1.0):.1f}"))  # I Solar
        self.lcdNumber_4.display(float(f"{p_grid/max(v,1.0):.1f}"))   # I Xarxa
        self.lcdNumber_5.display(float(f"{v:.2f}"))                 # V Bus
        self.lcdNumber_12.display(float(f"{i_net:.1f}"))             # I Net (Cap)
        self.lcdNumber_13.display(float(f"{i_loads[0]:.1f}"))        # Duty Cycle Càrrega 1 (%)
        self.lcdNumber_14.display(float(f"{i_loads[1]:.1f}"))        # Duty Cycle Càrrega 2 (%)
        self.lcdNumber_15.display(float(f"{i_loads[2]:.1f}"))        # Duty Cycle Càrrega 3 (%)

        # Actualitzar indicadors visuals (LEDs Checkboxes)
        self.checkBox.setChecked(i_loads[0] > 0)     # Roig
        self.checkBox_3.setChecked(i_loads[1] > 0)   # Blau
        self.checkBox_2.setChecked(i_loads[2] > 0)   # Verd
        
        self.checkBox_7.setChecked(i_loads[0] > 0)   # Roig (Esquema)
        self.checkBox_8.setChecked(i_loads[1] > 0)   # Blau (Esquema)
        self.checkBox_9.setChecked(i_loads[2] > 0)   # Verd (Esquema)

        # Actualitzar Històrics
        self.h['vs'].append(sim_state['v_bus'])
        self.h['soc'].append(sim_state['soc'])
        self.h['ps'].append(data['p_solar'])
        self.h['pg'].append(data['p_grid'])
        # Potència de consum com a absorvida (negativa)
        self.h['pc'].append(-data['p_cons'])
        # Invertim el signe de i_net per visualitzar KCL (Suma = 0)
        self.h['in'].append(-sim_state['i_net'])
        # Potència del condensador: negativa si absorbeix (carrega), positiva si entrega
        self.h['pcp'].append(-p_cap)
        # Keep Solar and Grid as current (A)
        self.h['is'].append(data['p_solar'] / max(sim_state['v_bus'], 10))
        self.h['ig'].append(data['p_grid'] / max(sim_state['v_bus'], 10))
        self.h['ic'].append(i_loads[0])   # Duty Cycle Roig (%)
        self.h['il2'].append(i_loads[1])  # Duty Blau (%)
        self.h['il3'].append(i_loads[2])  # Duty Verd (%)

        # Actualitzar Gràfics
        self.curve_vbus.setData(list(self.h['vs']))
        self.curve_soc.setData(list(self.h['soc']))
        self.curve_p_sol.setData(list(self.h['ps']))
        self.curve_p_grid.setData(list(self.h['pg']))
        self.curve_p_cons.setData(list(self.h['pc']))
        self.curve_p_cap.setData(list(self.h['pcp']))
        
        self.curve_i_sol.setData(list(self.h['is']))
        self.curve_i_grid.setData(list(self.h['ig']))
        self.curve_i_cons.setData(list(self.h['ic'])) # Plot duty cycle for load 1
        self.curve_i_load2.setData(list(self.h['il2']))
        self.curve_i_load3.setData(list(self.h['il3']))
        self.curve_i_net.setData(list(self.h['in']))

        # Actualitzar Gràfics Hardware (Scalant a 0-3.3V)
        if self.show_hw:
            v_d25 = (data['dac_pv'] / 255) * 3.3
            v_a35 = (data.get('adc_pv_raw', 0) / 4095) * 3.3
            v_d26 = (data.get('dac_grid_val', 0) / 255) * 3.3
            v_a32 = (data.get('adc_grid_raw', 0) / 4095) * 3.3
            v_a34 = (data.get('adc_raw', 0) / 4095) * 3.3
            
            loads = data.get('hw_loads', {'r':0, 'g':0, 'b':0})

            self.hw_h['d25'].append(v_d25)
            self.hw_h['a35'].append(v_a35)
            self.hw_h['d26'].append(v_d26)
            self.hw_h['a32'].append(v_a32)
            self.hw_h['a34'].append(v_a34)
            self.hw_h['p2'].append((loads['r']/255)*3.3)
            self.hw_h['p5'].append((loads['g']/255)*3.3)
            self.hw_h['p4'].append((loads['b']/255)*3.3)

            self.curve_d25.setData(list(self.hw_h['d25']))
            self.curve_a35.setData(list(self.hw_h['a35']))
            self.curve_d26.setData(list(self.hw_h['d26']))
            self.curve_a32.setData(list(self.hw_h['a32']))
            self.curve_a34.setData(list(self.hw_h['a34']))
            self.curve_p2.setData(list(self.hw_h['p2']))
            self.curve_p5.setData(list(self.hw_h['p5']))
            self.curve_p4.setData(list(self.hw_h['p4']))

    def close_all(self):
        self.graph_win.close()
        if self.show_hw:
            self.hw_win.close()
        self.close()

    def closeEvent(self, event):
        self.graph_win.close()
        if self.show_hw:
            self.hw_win.close()
        event.accept()

if __name__ == "__main__":
    import sys
    import random
    app = QtWidgets.QApplication(sys.argv)
    test_gui = GUI()
    test_gui.show()
    
    # Simular una actualització amb dades aleatòries
    d = {'p_solar': 500, 'p_grid': 100, 'p_cons': 300, 'v_bus_real': 405}
    s = {'v_bus': 400, 'soc': 75, 'i_net': 0.5}
    test_gui.update_view(d, s)
    
    sys.exit(app.exec_())