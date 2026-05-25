from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
from collections import deque
from ui import Ui_MainWindow

class GUI(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, show_hw=False):
        super().__init__()
        self.show_hw = show_hw
        self.setupUi(self)

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
        
        self.p3 = self.graph_win.addPlot(title="Balanç de Potències")
        self.p3.setLabel('left', "Potència", units='W')
        self.p3.addLegend()
        self.curve_p_sol = self.p3.plot(pen=pg.mkPen('orange', width=2), name='Solar')
        self.curve_p_grid = self.p3.plot(pen=pg.mkPen('cyan', width=2), name='Xarxa')
        self.curve_p_cons = self.p3.plot(pen=pg.mkPen('red', width=2), name='Consum')
        self.curve_p_cap = self.p3.plot(pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine), name='Capacitat')

        self.p4 = self.graph_win.addPlot(title="Intensitats de la Micro-xarxa")
        self.p4.setLabel('left', "Corrent", units='A')
        self.p4.addLegend()
        self.curve_i_sol = self.p4.plot(pen=pg.mkPen('orange', width=1), name='Solar (A)')
        self.curve_i_grid = self.p4.plot(pen=pg.mkPen('cyan', width=1), name='Xarxa (A)')
        self.curve_i_cons = self.p4.plot(pen=pg.mkPen('red', width=1), name='Consum (A)')
        self.curve_i_net = self.p4.plot(pen=pg.mkPen('w', style=QtCore.Qt.DashLine), name='I Net (Cap)')
        
        self.graph_win.show()
        
        self.h = {k: deque(maxlen=200) for k in ['vs','vr','soc','ps','pg','pc','in', 'is', 'ig', 'ic', 'pcp']}

    def _setup_hw_monitor(self):
        # Finestra per a senyals de baix nivell (Pins ESP32)
        self.hw_win = pg.GraphicsLayoutWidget(title="Monitorització de l'ESP32")
        self.hw_win.resize(400, 800)
        
        # DAC 25 (Solar)
        self.p_dac25 = self.hw_win.addPlot(title="Pin 25: DAC Solar (V)")
        self.p_dac25.setYRange(0, 3.3)
        self.curve_dac25 = self.p_dac25.plot(pen='orange')
        
        self.hw_win.nextRow()
        
        # DAC 26 (Xarxa)
        self.p_dac26 = self.hw_win.addPlot(title="Pin 26: DAC Xarxa (V)")
        self.p_dac26.setYRange(0, 3.3)
        self.curve_dac26 = self.p_dac26.plot(pen='cyan')
        
        self.hw_win.nextRow()
        
        # ADC 34 (Bus)
        self.p_adc34 = self.hw_win.addPlot(title="Pin 34: ADC Bus (V)")
        self.p_adc34.setYRange(0, 3.3)
        self.curve_adc34 = self.p_adc34.plot(pen='m')

        self.hw_win.show()
        self.hw_h = {k: deque(maxlen=200) for k in ['d25', 'd26', 'a34']}

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
        inputs = self.get_inputs()
        i_loads = []
        for i in range(3):
            if data['served'][i]:
                p_load = inputs['cons_sliders'][i] * 5
                i_loads.append(p_load / max(v, 1.0))
            else:
                i_loads.append(0.0)

        # 1. Secció de Potències (W)
        self.lcdNumber_6.display(int(p_solar))
        self.lcdNumber_7.display(int(p_grid))
        self.lcdNumber_9.display(int(p_solar + p_grid)) # Potència Disponible
        self.lcdNumber_10.display(int(p_cons))
        self.lcdNumber_16.display(int(p_cap))           # Potència Condensador

        # 2. Secció d'Estat (V / %)
        self.lcdNumber_8.display(float(f"{v:.2f}"))
        self.lcdNumber_11.display(int(soc))

        # 3. Corrents de càrrega (A)
        self.lcdNumber_1.display(float(f"{i_loads[0]:.1f}"))
        self.lcdNumber_2.display(float(f"{i_loads[1]:.1f}"))
        self.lcdNumber_3.display(float(f"{i_loads[2]:.1f}"))

        # 4. Esquema (Corrents A i Voltatge V)
        self.lcdNumber.display(float(f"{p_solar/max(v,1.0):.1f}"))  # I Solar
        self.lcdNumber_4.display(float(f"{p_grid/max(v,1.0):.1f}"))   # I Xarxa
        self.lcdNumber_5.display(float(f"{v:.2f}"))                 # V Bus
        self.lcdNumber_12.display(float(f"{i_net:.1f}"))             # I Net (Cap)
        self.lcdNumber_13.display(float(f"{i_loads[0]:.1f}"))        # I Càrrega 1
        self.lcdNumber_14.display(float(f"{i_loads[1]:.1f}"))        # I Càrrega 2
        self.lcdNumber_15.display(float(f"{i_loads[2]:.1f}"))        # I Càrrega 3

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
        
        self.h['is'].append(data['p_solar'] / max(sim_state['v_bus'], 10))
        self.h['ig'].append(data['p_grid'] / max(sim_state['v_bus'], 10))
        self.h['ic'].append(-data['p_cons'] / max(sim_state['v_bus'], 10))

        # Actualitzar Gràfics
        self.curve_vbus.setData(list(self.h['vs']))
        self.curve_soc.setData(list(self.h['soc']))
        self.curve_p_sol.setData(list(self.h['ps']))
        self.curve_p_grid.setData(list(self.h['pg']))
        self.curve_p_cons.setData(list(self.h['pc']))
        self.curve_p_cap.setData(list(self.h['pcp']))
        
        self.curve_i_sol.setData(list(self.h['is']))
        self.curve_i_grid.setData(list(self.h['ig']))
        self.curve_i_cons.setData(list(self.h['ic']))
        self.curve_i_net.setData(list(self.h['in']))

        # Actualitzar Gràfics Hardware (Scalant a 0-3.3V)
        if self.show_hw:
            v_d25 = (data['dac_pv'] / 255) * 3.3
            v_d26 = (data['dac_grid'] / 255) * 3.3
            v_a34 = (data['adc_raw'] / 4095) * 3.3

            self.hw_h['d25'].append(v_d25)
            self.hw_h['d26'].append(v_d26)
            self.hw_h['a34'].append(v_a34)

            self.curve_dac25.setData(list(self.hw_h['d25']))
            self.curve_dac26.setData(list(self.hw_h['d26']))
            self.curve_adc34.setData(list(self.hw_h['a34']))

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