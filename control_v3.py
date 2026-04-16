import sys
import time
import serial
from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg


# ┌─────────────────────────────────────────┐
# │  CONFIGURATION (adjust as needed)       │
# └─────────────────────────────────────────┘

# Choose: True = real ESP32, False = simulation only
USE_SERIAL = False

# Serial port (change to your system)
SERIAL_PORT = "COM3"        # Windows
# SERIAL_PORT = "/dev/ttyUSB0"   # Linux
SERIAL_BAUD = 115200
SERIAL_TIMEOUT = 0.1        # crucial to avoid hanging

# ┌─────────────────────────────────────────┐
# │  UI IMPORT                               │
# └─────────────────────────────────────────┘

from ui_v2 import Ui_MainWindow


# ┌─────────────────────────────────────────┐
# │  MAIN WINDOW CLASS                       │
# └─────────────────────────────────────────┘

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        # --- Variables del sistema energètic ---
        self.solar           = 0
        self.diesel          = 0
        self.red             = 0
        self.blue            = 0
        self.green           = 0
        self.energia_pv      = 0
        self.energia_diesel  = 0
        self.carga_1         = 0
        self.carga_2         = 0
        self.carga_3         = 0
        self.generador_activat = False

        # --- Gráfica tiempo real (pyqtgraph) ---
        self.win_plot = pg.GraphicsLayoutWidget(title="Gráfica en tiempo real")
        self.plot = self.win_plot.addPlot(title="DDP en V / Balanç")
        self.curva = self.plot.plot(pen='y')

        # --- Datos de la gráfica ---
        self.dataN = []
        self.dataY = []
        self.lastN = 0

        # --- Temporizador de muestreo ---
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.muestreo)
        self.timer.start(100)   # 100 ms

        # --- Textos iniciales ---
        self.label.setText("Gestió Energètica: Balanç (Gen - Consum)")
        self.pushButton_1.setText("Boto Extra")
        self.pushButton_2.setText("Generador: OFF")

        # --- Conexiones de botones ---
        self.pushButton_1.clicked.connect(self.botonSerie)
        self.pushButton_2.clicked.connect(self.botonON)

        # --- Conexiones sliders CÀRREGA ---
        self.horizontalSlider_1.valueChanged.connect(self.leeCarga1)
        self.horizontalSlider_2.valueChanged.connect(self.leeCarga2)
        self.horizontalSlider_3.valueChanged.connect(self.leeCarga3)

        # --- Conexiones sliders GENERACIÓ ---
        self.verticalSlider_1.valueChanged.connect(self.leePV)
        self.verticalSlider_2.valueChanged.connect(self.leeDiesel)

    def muestreo(self):
        # --- Serial mode (if enabled) ---
        if USE_SERIAL and hasattr(self, "ser") and self.ser is not None:
            try:
                self.ser.write(b'V\r')
                texto = self.ser.readline()
                if texto:
                    try:
                        valor = float(texto)
                    except (ValueError, TypeError):
                        return
                    self.lcdNumber_8.display(valor)

                    # Update graph
                    self.dataY.append(valor)
                    self.dataN.append(self.lastN)
                    self.lastN += 1

                    if len(self.dataN) > 2000:
                        self.dataN = self.dataN[1:]
                        self.dataY = self.dataY[1:]

                    self.curva.setData(self.dataN, self.dataY)

            except (serial.SerialException, OSError):
                print("Error de puerto serial, cerrando.")
                self.ser.close()
                self.ser = None

            except Exception as e:
                print("Error interno de comunicación:", e)

        # --- Simulation mode (no serial) ---
        else:
            consum_total = self.carga_1 + self.carga_2 + self.carga_3
            gen_diesel    = self.energia_diesel if self.generador_activat else 0
            generacio_total = self.energia_pv + gen_diesel

            # Requisito: Carga 1 siempre cubierta
            if generacio_total < self.carga_1:
                falta = self.carga_1 - generacio_total
                if not self.generador_activat:
                    self.generador_activat = True
                    self.pushButton_2.setText("Generador: ON")

                nou_valor_diesel = self.energia_diesel + falta
                self.verticalSlider_2.setValue(int(nou_valor_diesel))
                generacio_total = self.energia_pv + self.energia_diesel

            balanc_net = generacio_total - consum_total
            self.lcdNumber_8.display(balanc_net)

            # Dummy "sensor" value for the plot
            valor = balanc_net
            self.dataY.append(valor)
            self.dataN.append(self.lastN)
            self.lastN += 1

            if len(self.dataN) > 2000:
                self.dataN = self.dataN[1:]
                self.dataY = self.dataY[1:]

            self.curva.setData(self.dataN, self.dataY)

    # -------------------------------------------------------------------
    #  Sliders CÀRREGA (loads)
    def leeCarga1(self, value):
        self.lcdNumber_1.display(value)
        if USE_SERIAL and hasattr(self, "ser") and self.ser is not None:
            self.ser.write(f"A{value}\r".encode('ascii'))
        else:
            self.red = value
            self.update_consum()

    def leeCarga2(self, value):
        self.lcdNumber_2.display(value)
        if USE_SERIAL and hasattr(self, "ser") and self.ser is not None:
            self.ser.write(f"A{value}\r".encode('ascii'))
        else:
            self.blue = value
            self.update_consum()

    def leeCarga3(self, value):
        self.lcdNumber_3.display(value)
        if USE_SERIAL and hasattr(self, "ser") and self.ser is not None:
            self.ser.write(f"A{value}\r".encode('ascii'))
        else:
            self.green = value
            self.update_consum()

    # -------------------------------------------------------------------
    #  Sliders GENERACIÓ (PV / Diesel)
    def leePV(self, value):
        self.lcdNumber_6.display(value)
        if USE_SERIAL and hasattr(self, "ser") and self.ser is not None:
            self.ser.write(f"A{value}\r".encode('ascii'))
        else:
            self.solar = value
            self.energia_pv = value
            self.update_power()

    def leeDiesel(self, value):
        self.lcdNumber_7.display(value)
        if USE_SERIAL and hasattr(self, "ser") and self.ser is not None:
            self.ser.write(f"A{value}\r".encode('ascii'))
        else:
            self.diesel = value
            self.energia_diesel = value
            self.update_power()

    # -------------------------------------------------------------------
    #  Power / consum update
    def update_power(self):
        powerIN = self.solar + self.diesel
        self.lcdNumber_9.display(powerIN)

    def update_consum(self):
        powerOUT = self.red + self.blue + self.green
        self.lcdNumber_10.display(powerOUT)

    # -------------------------------------------------------------------
    #  Boton ON/OFF Generador
    def botonON(self):
        if self.generador_activat:
            self.pushButton_2.setText("Generador: OFF")
            self.generador_activat = False
            if USE_SERIAL and hasattr(self, "ser") and self.ser is not None:
                self.ser.write(b'off\r')
        else:
            self.pushButton_2.setText("Generador: ON")
            self.generador_activat = True
            if USE_SERIAL and hasattr(self, "ser") and self.ser is not None:
                self.ser.write(b'on\r')

    # -------------------------------------------------------------------
    #  Botón extra (debug)
    def botonSerie(self):
        print("Botó extra premut.")
        if USE_SERIAL and hasattr(self, "ser") and self.ser is not None:
            self.ser.write(b'XXXX\r')


# ┌─────────────────────────────────────────┐
# │  SET UP SERIAL PORT                      │
# └─────────────────────────────────────────┘

def setup_serial():
    if USE_SERIAL:
        try:
            ser = serial.Serial(SERIAL_PORT, SERAL_BAUD, timeout=SERIAL_TIMEOUT)
            print(f"Puerto {SERIAL_PORT} abierto correctamente.")
            return ser
        except Exception as e:
            print(f"Error al abrir el puerto serial: {e}")
            return None
    else:
        print("Modo simulació (no serial).")
        return None


# ┌─────────────────────────────────────────┐
# │  MAIN ENTRY POINT (safe Ctrl+C)        │
# └─────────────────────────────────────────┘

if __name__ == "__main__":
    ser = setup_serial()

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.ser = ser   # attach to object so muestreo() can access it

    window.show()
    window.win_plot.show()

    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("\nInterrupción por Ctrl+C.")
    finally:
        if hasattr(window, "ser") and window.ser is not None:
            try:
                window.ser.write(b'off\r')
                time.sleep(0.2)
                window.ser.write(b'A0\r')
                time.sleep(0.2)
                window.ser.close()
                print("Puerto serial cerrado.")
            except Exception as e:
                print("Error al cerrar el puerto:", e)