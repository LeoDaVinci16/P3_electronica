from machine import Pin, DAC, ADC, PWM
import sys
import uselect
import time

# -----------------------
# CONFIGURACIÓ
# -----------------------
# Sortides analògiques (0-255)
dac_1 = DAC(Pin(25))
dac_2 = DAC(Pin(26))

# Sortida PWM (Pin 27) per emular la Xarxa
grid_out = PWM(Pin(27))
grid_out.freq(1000)

# Entrades analògiques (0-4095) per a monitorització
adc_bus = ADC(Pin(34))
adc_bus.atten(ADC.ATTN_11DB) # Fins a 3.3V

adc_pv = ADC(Pin(35))
adc_pv.atten(ADC.ATTN_11DB)

adc_grid = ADC(Pin(32))
adc_grid.atten(ADC.ATTN_11DB)

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
    while spoll.poll(0):
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
            elif linea.startswith('V'):
                v_grid = int(linea[1:])
                v_grid = max(0, min(255, v_grid))
                grid_out.duty(v_grid * 4) # Escalat de 8 a 10 bits (0-1023)
        except:
            pass

    # 2. Llegim els ADCs amb Oversampling (Mitjana de 16 mostres per reduir variació)
    def read_stable(adc):
        m = 0
        for _ in range(16):
            m += adc.read()
        return m >> 4 # Divisió per 16 ràpida

    v34 = read_stable(adc_bus)
    v35 = read_stable(adc_pv)
    v32 = read_stable(adc_grid)

    # 3. Enviem les dades al PC (Format: i1 i2 adc34 adc35 adc32)
    print(f"{i_1} {i_2} {v34} {v35} {v32}")

    # 4. Pausa més curta per reduir el delay (10ms = 100Hz)
    time.sleep_ms(10)