import csv
import os
import random

class Brain:
    def __init__(self):
        # Paràmetres del Control Proporcional de la Xarxa
        self.V_TARGET_GRID = 30.0
        self.KP_GRID = 100.0
        
        self.solar_data = self._load_solar_csv()
        self.idx = 0

    def _load_solar_csv(self):
        data = []
        try:
            path = os.path.join(os.path.dirname(__file__), 'irradiancia.csv')
            with open(path, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and row[0] and row[0][0].isdigit():
                        data.append((row[0], float(row[1])))
        except:
            data = [("20230101:0000", 500.0)]
        return data if data else [("20230101:0000", 500.0)]

    def process(self, gui_inputs, adc_raw, current_vbus):
        # 1. Obtenir Solar actual
        ts, p_solar = self.solar_data[self.idx]
        self.idx = (self.idx + 1) % len(self.solar_data)

        # 2. Lògica de Shedding
        # Càrrega 0 (Roig) és crítica. 1 i 2 es desconnecten si V < 30V
        served = [True, True, True]
        p_cons_pot = [s * 5 for s in gui_inputs['cons_sliders']] # Potència potencial
        
        if current_vbus < self.V_TARGET_GRID:
            served[1] = False 
            served[2] = False

        # 3. Potència de Xarxa
        v_grid_slider = gui_inputs['grid_slider']
        grid_forced_off = False
        # Protecció sobretensió: Desconnectem la xarxa manual si el bus supera els 35V
        if current_vbus > 35.0:
            p_grid_manual = 0
            grid_forced_off = True
        else:
            p_grid_manual = v_grid_slider * 10 # 0-255 -> 0-2550W (Només consum)
        
        # Suport automàtic: Entra si la càrrega crítica està ON i V < 30V
        is_red_active = gui_inputs['cons_sliders'][0] > 0
        p_grid_auto = 0
        if is_red_active and current_vbus < self.V_TARGET_GRID:
            # Càlcul de l'error i aplicació del guany proporcional
            error_v = self.V_TARGET_GRID - current_vbus
            p_grid_auto = error_v * self.KP_GRID
            
        p_grid = p_grid_manual + p_grid_auto

        # Consum real final
        p_cons = sum([p_cons_pot[i] for i in range(3) if served[i]])

        # 4. Escalar ADC Hardware
        # ADC (0-4095) -> Volts (0-50V)
        # Si adc_raw és 0 (GND), v_bus_real serà 0V
        v_bus_real = (adc_raw / 4095.0 * 50.0) if adc_raw is not None else current_vbus

        # 5. Protecció PV (Sobretensió)
        # Si el bus supera els 45V, tallem la injecció PV per protegir el hardware real.
        pv_forced_off = False
        if current_vbus > 45.0:
            pv_forced_off = True
            p_solar_effective = 0.0
        else:
            p_solar_effective = p_solar

        # 6. Calcular valors per als DACs
        # DAC A (Pin 25): Fotovoltaica (0-1000W -> 0-255)
        dac_pv = int(max(0, min(255, (p_solar_effective / 1000.0) * 255.0)))
        # DAC B (Pin 26): Xarxa (Manual + Automàtic de seguretat)
        # El DAC de xarxa reflecteix el slider + l'ajuda automàtica
        dac_grid = int(max(0, min(255, (v_grid_slider if not grid_forced_off else 0) + (p_grid_auto / 10.0))))

        return {
            'p_solar': p_solar_effective, 'p_grid': p_grid, 'p_cons': p_cons,
            'v_bus_real': v_bus_real, 'served': served,
            'dac_pv': dac_pv, 'dac_grid': dac_grid,
            'adc_raw': adc_raw if adc_raw is not None else 0,
            'grid_forced_off': grid_forced_off, 'pv_forced_off': pv_forced_off,
            'timestamp': ts
        }

if __name__ == "__main__":
    b = Brain()
    # Comencem a l'índex 8 perquè les primeres hores del CSV són nit (0.0W)
    b.idx = 8 
    dummy_gui = {'grid_slider': 200, 'cons_sliders': [10, 10, 10]}
    res = b.process(dummy_gui, 2048, 40.0)
    print(f"Resultats del Brain (Pas {b.idx-1}):")
    for k, v in res.items():
        print(f"  {k}: {v}")
    
    res2 = b.process(dummy_gui, 2048, 40.0)
    print(f"Següent P_Solar (Pas {b.idx-1}): {res2['p_solar']} (Ara hauria de ser diferent)")