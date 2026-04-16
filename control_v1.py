# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
from PyQt5.QtCore import QTimer
from control_ui_v1 import *
class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow): 
    def __init__(self, *args, **kwargs):
        QtWidgets.QMainWindow.__init__(self, *args, **kwargs)
        self.setupUi(self) 
          
        # Variables del sistema energètic
        self.energia_pv = 0
        self.energia_diesel = 0
        self.carga_1 = 0
        self.carga_2 = 0
        self.carga_3 = 0

        # inicio el temporizador o evento temporal y cargo la función a ejecutar MUESTREO
        self.timer = QTimer()
        self.timer.timeout.connect(self.muestreo)
        self.timer.start(100)   # Actualització de la gràfica cada 100ms

        # Editar los valores iniciales de las etiquetas que hay en la UI
        self.label.setText("Gestió Energètica: Balanç (Gen - Consum)")     
        self.pushButton_1.setText("Boto Extra")
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
        
        # 1. Calculem el consum total
        consum_total = self.carga_1 + self.carga_2 + self.carga_3
        
        # 2. Generació actual pre-càlcul
        generacio_diesel_actual = self.energia_diesel if self.generador_activat else 0
        generacio_total = self.energia_pv + generacio_diesel_actual
        
        # 3. RESTRICCIÓ: La Càrrega 1 sempre ha d'estar coberta
        if generacio_total < self.carga_1:
            # Calculem l'energia que falta
            falta = self.carga_1 - generacio_total
            
            # Si el generador està apagat, l'encenem automàticament
            if not self.generador_activat:
                self.generador_activat = True
                self.pushButton_2.setText("Generador: ON")
                
            # Calculem el nou valor on ha d'estar el slider del generador
            nou_valor_diesel = self.energia_diesel + falta
            
            # Movem el slider de la interfície AUTOMÀTICAMENT
            # Això dispararà la funció 'leeDiesel' per si sol i ens actualitzarà els LCDs
            self.verticalSlider_2.setValue(nou_valor_diesel)
            
            # Com que hem canviat el dièsel en aquest mateix cicle, actualitzem la generació
            generacio_total = self.energia_pv + self.energia_diesel
        
        # 4. El balanç net (Generació - Consum) totalment net, sense soroll
        balanc_net = generacio_total - consum_total
        
        self.lcdNumber_8.display(balanc_net)   # Mostrem el balanç al LCD gran
        
        # Agregamos los datos al array
        dataY.append(balanc_net)
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
    def leeCarga1(self, event):
        self.lcdNumber_1.display(event)
        self.carga_1 = event

    def leeCarga2(self, event):
        self.lcdNumber_2.display(event)
        self.carga_2 = event

    def leeCarga3(self, event):
        self.lcdNumber_3.display(event)
        self.carga_3 = event

    def leePV(self, event):
        self.lcdNumber_6.display(event)
        self.energia_pv = event

    def leeDiesel(self, event):
        self.lcdNumber_7.display(event)
        self.energia_diesel = event                               
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

