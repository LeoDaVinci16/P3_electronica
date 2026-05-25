from machine import Pin, DAC
from time import sleep

# -----------------------
# CONFIGURACIÓ
# ----------------------


VREF = 3.3 # V
IREF = 33 # mA
dac_max =255

dac_pin_1 = 25
dac_pin_2 = 26


i_1 = 255
i_2 = 255

bit_1 = i_1 * IREF / dac_max
bit_2 = i_2 * IREF / dac_max



SAMPLES = 11
DELAY = 0.005

# -----------------------
# INICIALITZACIÓ
# -----------------------


dac_1 = DAC(Pin(dac_pin_1))
dac_2 = DAC(Pin(dac_pin_2))


def bits_a_volts(bits):

    return bits * VREF / ADC_MAX

while True:
    dac_1.write(i_1)
    dac_2.write(i_2)
    print(f"Trying with \n - DAC 1 = {i_1} \n - DAC 2 = {i_2}")