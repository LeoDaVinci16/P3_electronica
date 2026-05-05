from machine import Pin, DAC
import sys

# -----------------------
# CONFIG
# -----------------------
dac_1 = DAC(Pin(25))
dac_2 = DAC(Pin(26))

i_1 = 0
i_2 = 0

print("READY")

# -----------------------
# LOOP
# -----------------------
while True:
    texto = sys.stdin.readline()  # wait for command

    if not texto:
        continue

    try:
        if texto[0] == 'A':   # DAC 1
            i_1 = int(texto[1:])
            if i_1 > 255: i_1 = 255
            if i_1 < 0: i_1 = 0
            dac_1.write(i_1)

        elif texto[0] == 'B': # DAC 2
            i_2 = int(texto[1:])
            if i_2 > 255: i_2 = 255
            if i_2 < 0: i_2 = 0
            dac_2.write(i_2)

        # optional feedback
        print(i_1, i_2)

    except:
        print("ERR")
