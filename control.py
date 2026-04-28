# -*- coding: utf-8 -*-
import pandas as pd
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
from collections import deque
from ui import Ui_MainWindow

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

                # ------------ DADES DE SOLAR ----------------
        self.V_bus = 10.0         # Tensió nominal (V)
        self.C = 50.0             # Capacitat ajustada per a corrents de max 25.5A
        self.dt = 1              # Pas de temps (en hores). 0.002h = 7.2s de simulació per pas.        
        self.speed = 50 # Velocitat de la simulació
                # To make simulation go faster, decrease this; to slow it down, increase it.
        self.escala_I = 0.1       # Factor de conversió: Slider 100 -> 10 Amperis
        
        try:
            nom_fitxer = 'irradiancia.csv'

            df = pd.read_csv(nom_fitxer, skiprows=8, skipfooter=10, engine='python')
            df['time'] = pd.to_datetime(df['time'], format='%Y%m%d:%H%M')
            
            # Filtre de setmana (168 hores)
            df_setmana = df.iloc[0:8760] 
            
            self.dades_irradiancia = df_setmana['G(i)'].values
            self.dades_temps = df_setmana['time'].dt.strftime('%Y%m%d:%H%M').values
            self.total_hores = len(self.dades_irradiancia)
            print(f"✅ Simulació 10V / 25A preparada: {self.total_hores} hores.")
        except Exception as e:
            print(f"❌ Error dades: {e}")
            self.dades_irradiancia = [0]*168
            self.dades_temps = ["00000000:0000"]*168


# =========================================================
# CONTROLLER
# =========================================================
class EnergyController:
    def compute(self, s):
        # Determine potential PV current based on irradiance
        i_pv_potential = s.pv if s.pv_on else 0
        load_amps = [l * s.escala_I for l in s.load]
        
        # 1. Load Shedding Logic
        # Load 0 (Red) is critical. Loads 1 & 2 are shed if V_bus drops
        # indicating PV + Condenser cannot satisfy the total demand.
        served = [True, False, False]
        
        # If the bus is well-charged (>10.5V), use stored energy for all loads
        if s.V_bus > 10.5:
            served = [True, True, True]
        # Otherwise, if voltage is healthy, allow them only if Solar can sustain them
        elif s.V_bus > 10.2:
            if i_pv_potential >= (load_amps[0] + load_amps[1] + load_amps[2]):
                served = [True, True, True]
            elif i_pv_potential >= (load_amps[0] + load_amps[1]):
                served = [True, True, False]

        # 2. Grid Compensation (Only for Red Load)
        # Grid kicks in only if V_bus < 10.0V. Since non-criticals shed at 10.1V,
        # the grid effectively only supports Load 0.
        i_grid = max(0, (10.0 - s.V_bus) * 15.0) if s.V_bus < 10.0 else 0

        return i_pv_potential, i_grid, served


# =========================================================
# MAIN WINDOW
# =========================================================
class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.state = EnergyState()
        # ----------------- SIMULATION TIME --------------------------        
        self.simulation_time = 0.0        
        self.dt = self.state.dt

        self.setupUi(self)

        for lcd in [self.lcdNumber_6, self.lcdNumber_7, self.lcdNumber_9, self.lcdNumber_10,
                    self.lcdNumber_1, self.lcdNumber_2, self.lcdNumber_3,
                    self.lcdNumber, self.lcdNumber_4, self.lcdNumber_12,
                    self.lcdNumber_13, self.lcdNumber_14, self.lcdNumber_15]:
            lcd.setDigitCount(5)

        from PyQt5 import QtGui

        def set_lcd_color(lcd, color):
            pal = lcd.palette()
            pal.setColor(QtGui.QPalette.WindowText, QtGui.QColor(color))
            lcd.setPalette(pal)
            lcd.setStyleSheet("")
            lcd.setSegmentStyle(QtWidgets.QLCDNumber.Flat)

        set_lcd_color(self.lcdNumber_1, "red")
        set_lcd_color(self.lcdNumber_2, "blue")
        set_lcd_color(self.lcdNumber_3, "green")

        self.lcdNumber_8.setDigitCount(5) # Bus Voltage (e.g. 10.00)

        self.controller = EnergyController()

        # History deques for plotting
        self.hist_vbus = deque(maxlen=500)
        self.hist_soc = deque(maxlen=200)
        self.hist_solar = deque(maxlen=200)
        self.hist_grid = deque(maxlen=200)
        self.hist_cons = deque(maxlen=200)

        QtCore.QTimer.singleShot(0, self.step)

        self.index_hora = 0 
        self.corrent_pv = 0
        self.corrent_xarxa = 0
        self.carga_1 = self.carga_2 = self.carga_3 = 0
        self.xarxa_conectada = False

        # ---------------- GRAPH WINDOW ----------------
        self.graph_win = pg.GraphicsLayoutWidget(title="Monitorització de la Micro-xarxa")
        self.graph_win.resize(1000, 800)

        # Plot 1: Voltage
        self.p1 = self.graph_win.addPlot(title="Tensió del Bus (V)")
        self.p1.showGrid(x=True, y=True)
        self.curve_vbus = self.p1.plot(pen='y')
        
        self.graph_win.nextRow()
        
        # Plot 2: SoC
        self.p2 = self.graph_win.addPlot(title="Estat de Càrrega SoC (%)")
        self.p2.showGrid(x=True, y=True)
        self.p2.setYRange(0, 100)
        self.curve_soc = self.p2.plot(pen='g')
        
        self.graph_win.nextRow()
        
        # Plot 3: Powers (W)
        self.p3 = self.graph_win.addPlot(title="Potències (W)")
        self.p3.showGrid(x=True, y=True)
        self.p3.addLegend()
        self.curve_solar = self.p3.plot(pen=pg.mkPen('orange', width=2), name='Solar')
        self.curve_grid = self.p3.plot(pen=pg.mkPen('cyan', width=2), name='Xarxa')
        self.curve_cons = self.p3.plot(pen=pg.mkPen('red', width=2), name='Consum')

        self.graph_win.show()
        # ---------------- TIMER ----------------
        self.timer = QTimer()
        self.timer.timeout.connect(self.step)

        # Real-time interval between steps (ms). 
        self.timer.start(self.state.speed) 

        # ---------------- INPUTS ----------------
        self.horizontalSlider_1.valueChanged.connect(lambda v: self.set_load(0, v))
        self.horizontalSlider_2.valueChanged.connect(lambda v: self.set_load(1, v))
        self.horizontalSlider_3.valueChanged.connect(lambda v: self.set_load(2, v))

        self.verticalSlider_2.valueChanged.connect(self.set_grid)

        self.pushButton_3.clicked.connect(self.closeAll)

    # ----------------------- LED INDICATORS --------------
        self.state.load = [0, 0, 0]
        self.state.pv = 0
        self.state.grid = 0

        self.horizontalSlider_1.setValue(0)
        self.horizontalSlider_2.setValue(0)
        self.horizontalSlider_3.setValue(0)

        self.verticalSlider_2.setValue(0)

    # =====================================================
    # SIMULATION LOOP
    # =====================================================
    def step(self):
        # 1. Update state from irradiance data before computing logic
        # Synchronize: index_hora only increments when simulation_time crosses an hour boundary
        self.index_hora = int(self.simulation_time) % self.state.total_hores
        
        irr = self.state.dades_irradiancia[self.index_hora]
        self.state.pv = (irr / 1000.0) * 25.5  # Max 25.5A at peak irradiance

        # 2. Run controller (returns i_pv, i_grid, enabled_loads)
        i_pv_potential, i_grid, served = self.controller.compute(self.state)

        self.state.grid = i_grid

        # Update UI slider for grid support visual feedback
        self.verticalSlider_2.blockSignals(True)
        self.verticalSlider_2.setValue(int(i_grid / self.state.escala_I))
        self.verticalSlider_2.blockSignals(False)

        effective_load = [
            self.state.load[i] if served[i] else 0
            for i in range(3)
        ]

        # Inverter Control: Throttle PV if voltage exceeds safe limits
        i_pv = i_pv_potential
        i_cons_total = sum(effective_load) * self.state.escala_I
        if self.state.V_bus >= 14.5:
            i_pv = min(i_pv_potential, i_cons_total)

        # --- Grid current ---
        # i_grid is already in Amperes from controller

        # --- Load current (only served loads) ---
        p_cons_total_w = (i_cons_total * self.state.V_bus)

        # --- Generation current ---
        i_gen_total = i_pv + i_grid
        p_gen_total_w = (i_gen_total * self.state.V_bus)

        # --- KCL ---
        i_net = i_gen_total - i_cons_total

        # --- Capacitor dynamics ---
        # dV = (I_net / C) * dt
        self.state.V_bus += (i_net / self.state.C) * self.state.dt
        # Límits de seguretat
        self.state.V_bus = max(0, min(self.state.V_bus, 15.0)) 

        # --- Protecció de sobre-tensió: Desconnexió solar si el bus està ple ---
        if self.state.V_bus >= 14.98 and i_pv > i_cons_total:
            if self.state.pv_on:
                self.toggle_pv()
        
        # --- Auto-reconnect: If load is present and voltage is safe ---
        if not self.state.pv_on and self.state.V_bus < 13.5 and i_cons_total > 0:
            self.toggle_pv()

        ts = self.state.dades_temps[self.index_hora]
        self.label_date.setText(f"Durada total: {self.simulation_time:.1f} h \n\nData: {ts[6:8]}/{ts[4:6]}/2023 {ts[9:11]}:00 h")

        # 4. LCDs (All Power values shown in W)
        p_solar_w = (i_pv * self.state.V_bus)
        p_grid_w = (i_grid * self.state.V_bus)  

        self.lcdNumber_6.display(float(f"{p_solar_w:.1f}"))
        self.lcdNumber_7.display(float(f"{p_grid_w:.1f}"))
        self.lcdNumber_8.display(float(f"{self.state.V_bus:.2f}"))
        self.lcdNumber_9.display(float(f"{p_gen_total_w:.1f}"))
        self.lcdNumber_10.display(float(f"{p_cons_total_w:.1f}"))
        self.lcdNumber_16.display(float(f"{(i_net * self.state.V_bus):.1f}"))    # Condenser power W

        # Display current in Amperes for individual loads (1, 2, 3)
        self.lcdNumber_1.display(effective_load[0] * self.state.escala_I) 
        self.lcdNumber_2.display(effective_load[1] * self.state.escala_I)
        self.lcdNumber_3.display(effective_load[2] * self.state.escala_I)

        # --- Schematic Displays (Esquema) ---
        self.lcdNumber.display(float(f"{p_solar_w:.1f}"))        # Solar power W
        self.lcdNumber_4.display(float(f"{p_grid_w:.1f}"))    # Grid power W
        self.lcdNumber_5.display(float(f"{self.state.V_bus:.2f}")) # Bus Voltage
        
        # SoC calculation (0-15V range mapped to 0-100%)
        soc = (self.state.V_bus / 15.0) * 100
        self.lcdNumber_11.display(float(f"{soc:.1f}"))
        self.lcdNumber_12.display(float(f"{(i_net):.1f}"))    # Condenser current
        
        self.lcdNumber_13.display(float(f"{effective_load[0] * self.state.escala_I:.1f}")) # Load 1 A
        self.lcdNumber_14.display(float(f"{effective_load[1] * self.state.escala_I:.1f}")) # Load 2 A
        self.lcdNumber_15.display(float(f"{effective_load[2] * self.state.escala_I:.1f}")) # Load 3 A

        self.checkBox.setChecked(self.state.load[0] > 0)
        self.checkBox_3.setChecked(self.state.load[1] > 0)
        self.checkBox_2.setChecked(self.state.load[2] > 0)

        self.checkBox_7.setChecked(self.state.load[0] > 0)
        self.checkBox_8.setChecked(self.state.load[1] > 0)
        self.checkBox_9.setChecked(self.state.load[2] > 0)

        # ---------------- GRAPH ----------------
        self.hist_vbus.append(self.state.V_bus)
        self.hist_soc.append(soc)
        self.hist_solar.append(p_solar_w)
        self.hist_grid.append(p_grid_w)
        self.hist_cons.append(p_cons_total_w)

        self.curve_vbus.setData(list(self.hist_vbus))
        self.curve_soc.setData(list(self.hist_soc))
        self.curve_solar.setData(list(self.hist_solar))
        self.curve_grid.setData(list(self.hist_grid))
        self.curve_cons.setData(list(self.hist_cons))

        # ------------- set led slider to 0 if it breaks ----------------
        sliders = [
            self.horizontalSlider_1,
            self.horizontalSlider_2,
            self.horizontalSlider_3]

        for i in (1, 2):
            if not served[i] and sliders[i].value() != 0:
                sliders[i].setValue(0)

        # time:
        self.simulation_time += self.dt
    # =====================================================
    # INPUT HANDLERS
    # =====================================================
    def set_load(self, i, value):
        self.state.load[i] = value

    def set_grid(self, value):
        self.state.grid_base = value

    # solar toggle WITH SLIDER RESET
    def toggle_pv(self):
        self.state.pv_on = not self.state.pv_on

        if not self.state.pv_on:
            self.state.pv = 0
            print("S'ha desconectat la FV")
        else:
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