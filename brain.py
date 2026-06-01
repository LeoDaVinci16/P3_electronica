import csv
import os
import random

class Brain:
    def __init__(self):
        # Paràmetres del Control Proporcional de la Xarxa
        self.V_TARGET_GRID = 35.0 # Ara coincideix amb la simulació
        self.KP_GRID = 500.0      # Guany més alt per a una resposta proporcional suau
        
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
        # Càrrega 0 (Roig) és crítica. 
        # Prioritats: 0: Crítica | 1: Variable (Blau) | 2: Variable + Dummy (Verd)
        served = [True, True, True]
        p_cons_pot = [s * 5 for s in gui_inputs['cons_sliders']] 

        if current_vbus < 38.0: served[2] = False # Shed Verd (No crític)
        if current_vbus < 36.0: served[1] = False # Shed Blau (No crític)

        # 3. Potència de Xarxa
        # El slider ara es tracta com un percentatge (0-100%)
        grid_slider_pct = gui_inputs['grid_slider']
        
        # Protecció: disminuïm la potència manual si pugem de 40V
        grid_throttle = 1.0
        if current_vbus > 40.0:
            grid_throttle = max(0.0, 1.0 - (current_vbus - 40.0) / 5.0)
        
        p_grid_manual = grid_slider_pct * 10 * grid_throttle
        
        # Suport automàtic per voltatge (Proporcional) per mantenir el Bus a 35V
        error_v = self.V_TARGET_GRID - current_vbus
        p_grid_auto = max(0, error_v * self.KP_GRID) if served[0] else 0
            
        p_grid = p_grid_manual + p_grid_auto

        # 4. Escalar ADC Hardware
        v_bus_real = (adc_raw / 4095.0 * 50.0) if adc_raw is not None else current_vbus

        # 5. Protecció Sobretensió (>45V)
        pv_forced_off = False
        if current_vbus > 45.0:
            served[2] = True
            p_cons_pot[2] = 500 # Forcem consum màxim per al càlcul de potència (100% duty)
            pv_forced_off = True
            p_solar_effective = 0.0
        else:
            p_solar_effective = p_solar

        # Consum real final
        p_cons = sum([p_cons_pot[i] for i in range(3) if served[i]])

        # 6. Calcular valors per als DACs
        dac_pv = int(max(0, min(255, (p_solar_effective / 1000.0) * 255.0)))
        
        # DAC Grid: Sumem manual + gap + auto i escalem (Max 1000W = 255 DAC)
        dac_grid = int(max(0, min(255, (p_grid / 1000.0) * 255.0)))

        return {
            'p_solar': p_solar_effective, 'p_grid': p_grid, 'p_cons': p_cons,
            'v_bus_real': v_bus_real, 'served': served,
            'dac_pv': dac_pv, 'dac_grid': dac_grid,
            'adc_raw': adc_raw if adc_raw is not None else 0,
            'grid_forced_off': grid_throttle == 0, 'pv_forced_off': pv_forced_off,
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