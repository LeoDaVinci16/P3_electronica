import serial

class ESP32Controller:
    def __init__(self, port="COM4", baud=115200):
        try:
            self.ser = serial.Serial(port, baud, timeout=0.01)
            print(f"Connectat a ESP32 a {port}")
        except Exception as e:
            print(f"Error Sèrie: {e}")
            self.ser = None

    def send_data(self, dac_a, dac_b, v_sim_scaled=None):
        if self.ser:
            try:
                self.ser.write(f"A{int(dac_a)}\n".encode())
                self.ser.write(f"B{int(dac_b)}\n".encode())
                if v_sim_scaled is not None:
                    self.ser.write(f"V{int(v_sim_scaled)}\n".encode())
            except: pass

    def read_adc(self):
        if not self.ser: return None
        try:
            # Buidem el buffer i ens quedem només amb l'última lectura completa
            if self.ser.in_waiting > 0:
                # Llegim tot el bloc de dades esperant al buffer
                raw_data = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
                # Separem per línies i busquem l'última que estigui completa
                lines = raw_data.strip().split('\n')
                for line in reversed(lines):
                    parts = line.split()
                    if len(parts) >= 3:
                        try:
                            return [int(p) for p in parts[2:]]
                        except ValueError:
                            continue
        except: pass
        return None

    def close(self):
        if self.ser:
            self.ser.close()

if __name__ == "__main__":
    import time
    dev = ESP32Controller()
    print("Provant comunicació (5 segons)...")
    try:
        for _ in range(20):
            dev.send_data(128, 64) # Envia valors fixos als DACs
            adc = dev.read_adc()
            print(f"Lectura ADC Pin 34: {adc}")
            time.sleep(0.25)
    finally:
        dev.close()