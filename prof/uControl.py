"""
F. Casellas (GEEE: dic 2022) "uControl.py"

Ejemplo eco y control en BOOT salen ESP32 para el PC por puerto USB >> Control_XX.py
Desde SERIE para encender LED en GPIO02 y capturas tensión desde GPIO34

"""
from machine import Pin, PWM, UART, DAC, ADC    # carga la ESP32 al completo
from time import sleep
import sys         # Utiliza port 0 >> Rx a GPIO3 y Tx a GPIO1

num= 255
valorDc = 0
duty_u16 =0

# Configuraciones del ESP32
uart = UART(0,115200)

#led = Pin(2, Pin.OUT)   # Salida digital
ledA = PWM(Pin(2), 50, duty_u16=duty_u16)  # Salida PWM

dac1 = DAC(Pin(25))            # DAC 1 pin GPIO_25
dac1.write(128)                # Valor del DAC (128 -> 1.65V, sale 1,622V) (255 -> 3.3V sale 3,164V)

pin34 = Pin(34)                 # Defino el PIN34
adc34 = ADC(pin34)              # ADC en el PIN34
adc34.atten(ADC.ATTN_11DB)      # {0, 2_5, 6, 11} dB de atenuación con Vref = 1,1 V.
                                # Rango de lectura entre 0.0V y {1.0, 1.34, 2.0. 3,6} V
adc34.width(ADC.WIDTH_12BIT)    # Resolucion de {9, 10, 11, 12} bits

sleep(1)
num= 255
valorDc = 50
valorX = 1

print(' -dato- ')
# print( adc34.read())   # Lectura ADC directa
print( adc34.read_uv()/1000000)    # Presenta un valor en volts, corregido error de ADC
ledA.duty_u16(valorDc*661)

while True:
    texto = sys.stdin.readline() # espera a que llegue un texto terminado en \n
    # Procesa el TEXTO recibido
    if len(texto) > 0:
        if texto[0]=='A':           # LED A
            valorDc= int(texto[1:])
            if valorDc>99: valorDc=99   # detecta error por exceso >99%
            ledA.duty_u16(valorDc*661)
        elif texto[0]=='X':           # Generador X
            valorX= int(texto[1:])
            if valorX>255: valorX=255   # detecta error por exceso
            dac1.write(valorX)
        elif texto[0]=='V':        # lee ADC
            print( adc34.read_uv()/1000000)
        else:                 # Comando invalido
            print('tamanyo: ', len(texto), '   eco:', texto[0:-1])       # Incluye el CR y LF de la recepcion
    else: # no ha llegado ningun texto, no debe ejecutarse nunca
        sleep(0.01)  # espera Xs
        print('- ERROR -')
        
print('FIN')


