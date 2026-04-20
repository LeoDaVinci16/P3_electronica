# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
from PyQt5.QtCore import QTimer
from ui_v2 import *


# -------------------------------
# MODEL (no Qt here)
# -------------------------------
class EnergySystem:
    def __init__(self):
        self.carga = [0, 0, 0]
        self.pv = 0
        self.diesel = 0
        self.generador_on = False

    def total_load(self):
        return sum(self.carga)

    def total_generation(self):
        return self.pv + (self.diesel if self.generador_on else 0)


# -------------------------------
# UI (your existing class)
# -------------------------------
class DieselController:
    def update(self, system: EnergySystem):
        if system.total_generation() < system.carga[0]:
            deficit = system.carga[0] - system.total_generation()
            system.generador_on = True
            system.diesel += deficit



class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow): 
    def __init__(self, *args, **kwargs):
        QtWidgets.QMainWindow.__init__(self, *args, **kwargs)

        self.system = EnergySystem()
        self.controller = DieselController()   




        self.setupUi(self) 

        # inicio el temporizador o evento temporal y cargo la función a ejecutar MUESTREO
        self.timer = QTimer()
        self.timer.timeout.connect(self.muestreo)
        self.timer.start(100)   # Actualització de la gràfica cada 100ms

        # Editar los valores iniciales de las etiquetas que hay en la UI
        self.label.setText("Solar: ")     
        self.pushButton_1.setText("Solar ON")
        self.pushButton_2.setText("Generador: OFF")   
        self.generador_activat = False
        
        # Crear las conexiones de los eventos botones
        self.pushButton_1.clicked.connect(self.botonSerie)   
        self.pushButton_2.clicked.connect(self.botonON)
        
        # Connexions dels sliders de CONSUM (Càrregues) als respectius LCDs i funcions
        self.horizontalSlider_1.valueChanged.connect(self.leeCarga1)
        self.horizontalSlider_2.valueChanged.connect(self.leeCarga2)
        self.horizontalSlider_3.valueChanged.connect(self.leeCarga3)
        
        # Connexions dels sliders de GENERACIÓ als respectius LCDs i funcions
        self.verticalSlider_1.valueChanged.connect(self.leePV)
        self.verticalSlider_2.valueChanged.connect(self.leeDiesel)



    # --- FUNCIÓ DE MOSTREIG (BALANÇ I CONTROL AUTOMÀTIC DIÈSEL) ---


    def muestreo(self):   
        global curva, dataN, dataY, lastN

        #controler
        self.controller.update(self.system)

        #compute values
        generacion = self.system.total_generation()
        consumo = self.system.total_load()
        balance = generacion - consumo
        
        # update UI
        self.lcdNumber_8.display(balance)

        if self.system.generador_on:
            self.pushButton_2.setText("Generador: ON")
        else:
            self.pushButton_2.setText("Generador: OFF")

        def botonON(self):
            self.system.generador_on = not self.system.generador_on

        
        self.lcdNumber_8.display(balance)   # Mostrem el balanç al LCD gran
        
        # Agregamos los datos al array
        dataY.append(balance)
        dataN.append(lastN)
        lastN += 1

        # Limitamos a mostrar solo 200 muestras per veure bé els canvis
        if len(dataN) > 200:
            dataY = dataY[1:-1]
            dataN = dataN[1:-1]

        # Actualizamos los datos y refrescamos la gráfica
        curva.setData(dataN, dataY)     
        QtWidgets.QApplication.processEvents()   
        # --- FUNCIONS DELS SLIDERS ---
    def leeCarga1(self, value):
        self.lcdNumber_1.display(value)
        self.system.carga[0] = value

    def leeCarga2(self, value):
        self.lcdNumber_2.display(value)
        self.system.carga[1] = value

    def leeCarga3(self, value):
        self.lcdNumber_3.display(value)
        self.system.carga[2] = value

    def leePV(self, value):
        self.lcdNumber_6.display(value)
        self.system.pv = value

    def leeDiesel(self, value):
        self.lcdNumber_7.display(value)
        self.system.diesel = value         
                          
    def botonON(self):       
        if not self.generador_activat:
            self.pushButton_2.setText("Generador: ON") 
            self.generador_activat = True
        else:
            self.pushButton_2.setText("Generador: OFF") 
            self.generador_activat = False
        
    def botonSerie(self):       
        print('Botó per defecte premut.')

# Pantalla auxiliar per la gràfica
app = QtWidgets.QApplication.instance()
if app is None:
    app = QtWidgets.QApplication([])

# --- NOU CODI: Utilitzem GraphicsLayoutWidget ---
win = pg.GraphicsLayoutWidget(title="Balanç Energètic del Sistema")     
win.show() # Ara cal indicar explícitament que la mostri
p = win.addPlot(title="Balanç Net (Generació - Consum)")                
# ------------------------------------------------
curva = p.plot(pen='y')
p.enableAutoRange(axis='y') # Ajustament automàtic a la gràfica Y

dataN = [] 
dataY = []  
lastN = 0

# Aqui se abre la UI
if __name__ == "__main__":  
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()

