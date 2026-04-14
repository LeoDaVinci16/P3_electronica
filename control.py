"""
F. Casellas (GEEE: dic 2022)

Los datos y el control con ESP32 por puerto USB uControl_XX.py en run
Mejor poner el programa XXX en el boot

Referencias:
    PyQt 5 >>   https://doc.qt.io/
                https://www.riverbankcomputing.com/static/Docs/PyQt5/
                https://www.pyqtgraph.org/
                https://pyqtgraph.readthedocs.io/en/latest/
    Artículos >>https://pythonpyqt.com/contents/
    Ejemplos >> https://pythonpyqt.com/qtimer/
                https://www.laboratoriogluon.com/pyqtgraph-graficas-tiempo-real-con-python/
                https://web.archive.org/web/20080412230517/http://bulma.net/impresion.phtml?nIdNoticia=2336

 Detalles del proceso en:
    https://unipython.com/pyqt5-interfaces-graficas-con-python/
    https://medium.com/@hektorprofe/primeros-pasos-en-pyqt-5-y-qt-designer-programas-gr%C3%A1ficos-con-python-6161fba46060    
1.- ejecutar designer desde consola o desde acceso directo
2.- generar fichero Python en carpeta de trabajo con consola Anaconda-Navigator >> pyuic5 -x pru.ui -o ventana_ui.py
3.- programar en Python los métodos para cargar las librerías
4.- cargar la interfaz UI: etiquetas, conexiones y funcionalidades
5.- programar el resto de la aplicación
"""
from PyQt5 import QtWidgets, QtCore, QtGui
#from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import serial, time, random, sys


USE_SERIAL = False

# Aqui comienzan los métodos del UI
from control_v1 import *  # importo todo lo declarado en la UI
from PyQt5.QtCore import QTimer # importo temporizador


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow): # Constructor de mi ventana
    def __init__(self, *args, **kwargs):
        QtWidgets.QMainWindow.__init__(self, *args, **kwargs)
        self.setupUi(self) 
          
        # inicio el temporizador o evento temporal y cargo la función a ejecutar MUESTREO
        self.timer=QTimer()
        self.timer.timeout.connect(self.muestreo)
        self.timer.start(1000)   # en ms
        self.timer.setInterval(100)

        
        # Editar los valores iniciales de las etiquetas que hay en la UI
        #MainWindow.setObjectName("GEEE: Práctica gestión")
        #_translate = QtCore.QCoreApplication.translate
        #MainWindow.setWindowTitle(_translate("MainWindow", "GEEE: Práctica gestión"))
        self.label.setText("Práctica 3: control")     
        self.pushButton_1.setText("Lee serie")
        self.pushButton_2.setText("PWM1:off")   
        #self.lcdNumber_1.setObjectName("lcdNumber_1")            
        
        # Crear las conexiones de los eventos botones con las funcionalidades
        self.pushButton_1.clicked.connect(self.botonSerie)   
        self.pushButton_2.clicked.connect(self.botonON)
        
        # Se conecta el evento SLIDER con la acción leeLEDa donde estará LCD
        self.horizontalSlider_1.valueChanged.connect(self.leeLEDa)
        self.horizontalSlider_2.valueChanged.connect(self.leeLEDb)
        self.horizontalSlider_3.valueChanged.connect(self.leeLEDc)
        
        self.verticalSlider_1.valueChanged.connect(self.leeLEDx)
        self.verticalSlider_2.valueChanged.connect(self.leeLEDy)

        #self.grafica = Canvas_grafica()
        #self.ui.grafica.addWidget(self.grafica)
        
        self.solar = 0
        self.diesel = 0

        self.red = 0
        self.blue = 0
        self.green = 0
           
    # Crear nuevas funcionalidades 
    """ def muestreo(self):   # Mide periodicamente la tension
        ser.write(b'V\r')    # solicita el dato siguiente
        global curva, dataN, dataY, lastN, nuevoDato
        
        while(ser.in_waiting > 1):
            # Lee dato del buffer hasta que encuentra un CR '\n'
            texto = ser.readline()
            try:    # cuidado aparece texto sin numero y genera error
                valor=float(texto)  # la conversion problematica
            except:
                print('ERROR número:', texto)
                self.label.setText(texto.decode('Ascii'))# se pasa EVENT del SERIE a la etiqueta
            else:
                self.lcdNumber_8.display(valor)   # se pasa EVENT del SERIE al LCD
                #Agregamos los datos al array
                dataY.append(valor)
                dataN.append(lastN)
                lastN = lastN + 1

                # Limitamos a mostrar solo 2000 muestras
                if len(dataN) > 2000:
                    dataY = dataY[1:-1]
                    dataN = dataN[1:-1]

                #Actualizamos los datos y refrescamos la gráfica.
                curva.setData(dataN, dataY)     # eje horizontal, eje vertical
                QtGui.QApplication.processEvents() """   

    def muestreo(self):
        global curva, dataN, dataY, lastN

        if USE_SERIAL and ser:
            try:
                ser.write(b'V\r')
                texto = ser.readline()

                try:
                    valor = float(texto)
                except:
                    return

            except:
                return

        else:
            # SIMULATION (fake sensor)
            valor = self.solar * random.random() 

        self.lcdNumber_8.display(valor)

        dataY.append(valor)
        dataN.append(lastN)
        lastN += 1

        if len(dataN) > 2000:
            dataN = dataN[1:]
            dataY = dataY[1:]

        curva.setData(dataN, dataY)
                               
    def leeLEDa(self,event):
        self.lcdNumber_1.display(event)   # se pasa EVENT del SLIDER al LCD
        if USE_SERIAL and ser:
            ser.write(bytes('A'+str(event)+'\r','ascii'))
        else:
            print("Red", event)
            self.red = event
            self.update_consum()
    def leeLEDb(self,event):
        self.lcdNumber_2.display(event)   # se pasa EVENT del SLIDER al LCD
        if USE_SERIAL and ser:
            ser.write(bytes('A'+str(event)+'\r','ascii'))
        else:
            print("Blue", event)
            self.blue = event
            self.update_consum()
    def leeLEDc(self,event):
        self.lcdNumber_3.display(event)   # se pasa EVENT del SLIDER al LCD
        if USE_SERIAL and ser:
            ser.write(bytes('A'+str(event)+'\r','ascii'))
        else:
            print("Green", event)
            self.green = event
            self.update_consum()

    def leeLEDx(self,event):
        self.lcdNumber_6.display(event)   # se pasa EVENT del SLIDER al LCD
        #print(event)   # Muestra el dato EVENT en la pantalla de la consola 
        if USE_SERIAL and ser:
            ser.write(bytes('A'+str(event)+'\r','ascii'))
        else:
            print("Solar", event)
            self.solar = event
            self.update_power()
    def leeLEDy(self,event):
        self.lcdNumber_7.display(event)     # se pasa EVENT del SLIDER al LCD
        #print(event)   # Muestra el dato EVENT en la pantalla de la consola 
        if USE_SERIAL and ser:
            ser.write(bytes('A'+str(event)+'\r','ascii'))
        else:
            print("Diesel", event)
            self.diesel = event
            self.update_power()

    def update_power(self):
        powerIN = self.solar + self.diesel
        self.lcdNumber_9.display(powerIN)     # se pasa EVENT del SLIDER al LCD
        print("Power: ", powerIN)

    def update_consum(self):
        powerOUT = self.red+self.blue+self.green
        self.lcdNumber_10.display(powerOUT)
        print("Consum: ", powerOUT)

    def botonON(self):       
        global estado 
        if (estado == False):
            self.pushButton_2.setText("PWM1:on") 
            ser.write(b'on\r')
            estado = True
        else:
            self.pushButton_2.setText("PWM1:off") 
            ser.write(b'off\r')
            estado = False
        #print(estado)           
        
    def botonSerie(self):       
        #ser.write(b'XXXX\r')
        #ser.write(b'V\r')
        print('.')
  
        
        
# Aqui comienza el programa de control
# Abrimos un puerto serie
#ser = serial.Serial('/dev/ttyUSB0', 115200)
#ser = serial.Serial('/dev/ttyACM0', 115200)
#ser = serial.Serial('com3', 115200)

ser = None

if USE_SERIAL:
    ser = serial.Serial('COM3', 115200)

linea =b'off\r'       # El texto viaja en bytes, ejemplo de formato y de paso defino la variable. 
estado = False

# Pantalla auxiliar  
app = QtWidgets.QApplication([])
win = pg.GraphicsLayoutWidget(title="Gráfica en tiempo real")     #nombre de la ventana
p = win.addPlot(title="DDP en V")                #titulo de la grafica

curva = p.plot(pen='y')
# p.setRange(yRange=[0, 3.2])

dataN = [] # Vector de muestras
dataY = []  # Vector de valores
lastN = 0
num =0
nuevoDato = 0 

print("Hola arnau")

win.show()

# Aqui se abre la UI
if __name__ == "__main__":  
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()


# test signal (IMPORTANT)
curva.setData([0, 1, 2, 3], [0, 1, 0, 1])

sys.exit(app.exec_())

# Posproceso: cierra el LED y el puerto serie
ser.write(b'off\r')
time.sleep(0.2)
ser.write(b'A0\r')
time.sleep(0.2)
# No sabes la cantidad de bytes recibidos, utilizo tabulador CR y/o LF.
respuesta = ser.readline() 
texto = respuesta.decode('utf-8')     # Transforma los bytes en string
print('>>', texto)
print('- cierre -')
ser.close()
  



