from machine import Pin, DAC, ADC
import sys
import uselect
import time

# -----------------------
# CONFIGURACIÓ
# -----------------------
# Sortides analògiques (0-255)
dac_1 = DAC(Pin(25))
dac_2 = DAC(Pin(26))

# Entrada analògica (0-4095)
adc_1 = ADC(Pin(34))
adc_1.atten(ADC.ATTN_11DB) # Permet llegir fins a 3.3V aproximadament

i_1 = 0
i_2 = 0

# Configurem el poller per llegir el port sèrie sense bloquejar
spoll = uselect.poll()
spoll.register(sys.stdin, uselect.POLLIN)

print("ESP32 READY")

# -----------------------
# BUCLE PRINCIPAL
# -----------------------
while True:
    # 1. Mirem si hi ha ordres del PC (Sliders)
    while spoll.poll(0): # Fem un bucle per processar totes les ordres pendents
        linea = sys.stdin.readline().strip()
        try:
            if linea.startswith('A'):
                i_1 = int(linea[1:])
                i_1 = max(0, min(255, i_1))
                dac_1.write(i_1)
            elif linea.startswith('B'):
                i_2 = int(linea[1:])
                i_2 = max(0, min(255, i_2))
                dac_2.write(i_2)
        except:
            pass

    # 2. Llegim l'ADC del pin 34
    val_adc = adc_1.read()

    # 3. Enviem les dades al PC (Format: i1 i2 adc)
    # Aquest print és el que veuràs a la terminal del PC
    print(f"{i_1} {i_2} {val_adc}")

    # 4. Petita pausa per estabilitat (50ms = 20Hz)
    time.sleep_ms(50)