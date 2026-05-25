# Sistema SCADA de Control de Micro-xarxa (Simulació + Hardware)

Aquest projecte implementa un sistema de gestió energètica per a una micro-xarxa DC, combinant un motor de simulació física amb una implementació real mitjançant un microcontrolador ESP32. El sistema permet monitoritzar el balanç de potències, gestionar càrregues crítiques i controlar l'emmagatzematge d'energia.

## 📂 Estructura de Fitxers

```text
P3/
├── main.py              # Orquestrador per a l'ús amb Hardware Real al laboratori.
├── simulation.py        # Orquestrador per a Simulació Pura (100% Software).
├── hybrid.py            # Orquestrador Hardware-in-the-Loop (HIL) per a l'ESP32.
├── brain.py             # Cervell: Lògica de control, Shedding i presa de decisions.
├── gui.py               # Interfície gràfica PyQt5 i monitorització de hardware.
├── control_esp32.py     # Driver de comunicació sèrie (DAC/PWM/ADC) per al PC.
├── ui.py                # Classe d'interfície generada (QtDesigner).
├── irradiancia.csv      # Dades d'irradiància solar de Barcelona (PVGiS).
└── uControl_0.py        # Firmware MicroPython per a l'ESP32 (amb oversampling).
```

## ⚡ Especificacions de la Micro-xarxa

El sistema simula i controla un bus de corrent continu amb els següents paràmetres:

*   **Tensió Nominal del Bus:** 40 V.
*   **Tensió Màxima de Seguretat:** 50 V (Límit físic del condensador).
*   **Emmagatzematge:** Condensador de 12.000 µF (12 mF).
*   **Generació FV:** Basada en dades reals del PVGiS (Barcelona), escalada a 1000W pic.
*   **Suport de Xarxa:** Font d'importació (només consum) de fins a 2550W.
*   **Càrregues:** 
    *   **Càrrega 1 (Roig):** Crítica.
    *   **Càrrega 2 (Blau) i 3 (Verd):** No crítiques (gestionades per Load Shedding).

### Dimensionament del Sistema
El sistema està dissenyat per a potències d'uns **2.5 kW**. La capacitat de **12 mF** s'ha modelat amb un comportament exponencial (incloent una resistència de pèrdues de 200Ω) per simular la realitat física. El SoC es calcula linealment: **0V = 0%** i **50V = 100%**.

## 🧠 Lògica de Control (brain.py)

### 1. Gestió de Càrregues (Load Shedding)
Si $V_{bus} < 30V$, el sistema força la desconnexió de les càrregues **Blava i Verda** i posa els seus lliscadors a 0.

### 2. Suport de Xarxa Elèctrica
*   **Mode Automàtic:** Si $V_{bus} < 30V$ i la càrrega roja està encesa, s'activa un control proporcional ($K_p=100$) per mantenir la tensió.
*   **Protecció per Sobretensió:** Si $V_{bus} > 35V$, la xarxa es desconnecta forçadament (slider a 0) per evitar sobrecarregar el condensador.

## 🖥️ Funcionament de l'SCADA (GUI)

*   **Balanç de Potències:** Convenció de signes on fonts (Solar/Xarxa) són positives i receptors (Consum/Càrrega Condensador) són negatius. La suma visual a la línia de zero valida la Llei de Kirchhoff.
*   **Data i Temps:** Sincronitzat amb el fitxer d'irradiància; mostra la durada de la prova i la data real de 2023.
*   **Monitor ESP32:** Gràfiques en volts (0-3.3V) per depurar DACs i ADCs.

## 🚀 Execució

### 1. Mode Simulació Pura (`simulation.py`)
Simulació numèrica d'Euler amb oversampling i filtratge de pèrdues. No requereix hardware.
```bash
python simulation.py
```

### Mode Hardware Real
Per utilitzar al laboratori amb el condensador real i l'ESP32.

1.  Carrega `uControl_0.py` a l'ESP32 (MicroPython).
2.  Connecta el Pin 25 (DAC Solar) i el Pin 26 (DAC Xarxa) al circuit de control.
3.  Connecta el Pin 34 (ADC) al divisor de tensió del bus.
4.  Executa a l'ordinador:

```bash
python main.py
```

## 🛠️ Requisits

*   Python 3.x
*   PyQt5
*   PyQtGraph
*   PySerial (per al mode hardware)
*   Pandas (per processar el CSV d'irradiància)

---
*Projecte realitzat per Guillem Castillo i Arnau Coronado.*