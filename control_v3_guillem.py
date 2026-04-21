import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
from PyQt5.QtCore import QTimer
from ui_v3 import *
class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow): 
    def __init__(self, *args, **kwargs):
        QtWidgets.QMainWindow.__init__(self, *args, **kwargs)
        self.setupUi(self) 
        
        # --- PARÀMETRES DEL MODEL FÍSIC ESCALAT (10V) ---
        self.V_bus = 10.0          # Tensió inicial (V)
        self.V_ref = 10.0          # Referència de 10V
        self.C = 5.0               # Capacitat ajustada per a corrents de max 25.5A
        self.dt = 0.02             # Pas de temps (20ms)
        self.escala_I = 0.1        # Factor de conversió: Slider 255 -> 25.5 Amperis
        # ------------------------------------------------
        
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

        self.timer = QTimer()
        self.timer.timeout.connect(self.muestreo)
        self.timer.start(20) 

        #self.pushButton_2.setText("Xarxa: OFF")
        self.horizontalSlider_1.valueChanged.connect(self.leeCarga1)
        self.horizontalSlider_2.valueChanged.connect(self.leeCarga2)
        self.horizontalSlider_3.valueChanged.connect(self.leeCarga3)
        #self.pushButton_2.clicked.connect(self.botonON)
        self.verticalSlider_2.valueChanged.connect(self.leeXarxa)

    def leeCarga1(self, val): self.carga_1 = val; self.lcdNumber_1.display(val)
    def leeCarga2(self, val): self.carga_2 = val; self.lcdNumber_2.display(val)
    def leeCarga3(self, val): self.carga_3 = val; self.lcdNumber_3.display(val)
    def leeXarxa(self, val): self.corrent_xarxa = val; self.lcdNumber_7.display(val)

    def muestreo(self):   
        global curva, dataN, dataY, lastN
        
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
        
        # 5. Gràfica
        dataY.append(self.V_bus)
        dataN.append(lastN)
        lastN += 1
        if len(dataN) > 1000:
            dataY.pop(0)
            dataN.pop(0)
        curva.setData(dataN, dataY)

        self.index_hora = (self.index_hora + 1) % self.total_hores

    def botonON(self):       
        self.xarxa_conectada = not self.xarxa_conectada
        #self.pushButton_2.setText(f"Xarxa: {'ON' if self.xarxa_conectada else 'OFF'}")

if __name__ == "__main__":
    app = QtWidgets.QApplication.instance()
    if app is None: app = QtWidgets.QApplication([])
    win = pg.GraphicsLayoutWidget(title="Micro-xarxa 10V DC")     
    win.show()
    p = win.addPlot(title="Tensió del Bus (V)")                
    p.setYRange(0, 15)
    curva = p.plot(pen='g')
    dataN, dataY, lastN = [], [], 0
    window = MainWindow()
    window.show()
    app.exec_()