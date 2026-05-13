from machine import Pin, DAC, ADC  # Importem ADC
import sys
import uselect # Per llegir el port sèrie sense bloquejar el codi

# -----------------------
# CONFIG
# -----------------------
dac_1 = DAC(Pin(25))
dac_2 = DAC(Pin(26))

# El pin 34 és un ADC. Configurem l'atenuació per llegir fins a 3.6V
adc_1 = ADC(Pin(34))
adc_1.atten(ADC.ATTN_11DB) 

i_1 = 0
i_2 = 0

# Configurem el poller per llegir de sys.stdin sense aturar el bucle
spoll = uselect.poll()
spoll.register(sys.stdin, uselect.POLLIN)

print("READY")

# -----------------------
# LOOP
# -----------------------
while True:
    # Mirem si hi ha alguna comanda nova de l'ordinador (sense bloquejar)
    if spoll.poll(0): 
        texto = sys.stdin.readline().strip()
        
        try:
            if texto.startswith('A'):
                i_1 = int(texto[1:])
                i_1 = max(0, min(255, i_1)) # Limitem entre 0 i 255
                dac_1.write(i_1)

            elif texto.startswith('B'):
                i_2 = int(texto[1:])
                i_2 = max(0, min(255, i_2))
                dac_2.write(i_2)
        except:
            pass # Si la dada és errònia, no fem res

    # Llegim l'ADC (valor entre 0 i 4095)
    val_adc = adc_1.read()

    # ENVIEM LES DADES: El PC espera "i1 i2 adc"
    # Utilitzem un format d'espais per facilitar el line.split() del Python
    print(f"{i_1} {i_2} {val_adc}")