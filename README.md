# SCADA Micro-grid: Gestió Ciber-Física de Tercer Nivell

Aquest projecte consisteix en el disseny i implementació d'un sistema SCADA (Supervisory Control and Data Acquisition) per a la gestió de tercer nivell d'una micro-xarxa híbrida DC. El sistema combina un model de simulació dinàmica amb una planta física real controlada per un ESP32, permetent monitoritzar i gestionar el balanç entre generació renovable, suport de xarxa i consum intel·ligent.

## Objectiu del Projecte
L'objectiu principal és mantenir l'estabilitat d'un bus de tensió (consigna de **40V**) mitjançant la coordinació de fonts intermitents i la priorització de càrregues crítiques. El sistema és capaç de validar algorismes de control en tres escenaris: simulació pura, Hardware-in-the-Loop (HIL) i operació real.

---

## Estructura del Repositori

El programari està modularitzat per separar la interfície, la intel·ligència i la comunicació:

| Fitxer | Funció |
| :--- | :--- |
| `main.py` | **Orquestrador Real**. Executa el SCADA connectat a la micro-xarxa física. |
| `hybrid.py` | **Mode HIL**. Tanca un bucle DAC-ADC a l'ESP32 per validar latències. |
| `simulation.py` | **Motor de Física**. Resol les equacions del bus (Mètode d'Euler). |
| `brain.py` | **The Brain**. Conté la lògica de decisió (Load Shedding, Grid Support). |
| `uControl_0.py` | **Firmware**. Codi MicroPython per a l'ESP32 (Filtrat i PWM). |
| `control_esp32.py` | **Capa de Comunicació**. Gestiona el protocol sèrie i buida de buffers. |
| `gui.py` / `ui.py` | **Interfície Gràfica**. Dashboard SCADA creat amb PyQt5 i pyqtgraph. |
| `irradiancia.csv` | **Dades de Generació**. Dataset real de radiació per emular el sol. |

---

## Estructura de la Micro-xarxa

La infraestructura física (emulada i real) es basa en els següents components:

### 1. Maquinari (ESP32)
- **Bus DC**: Rang operatiu de 0-50V (sensat via ADC Pin 34).
- **Generació**: Solar (DAC Pin 25) i suport de Xarxa (DAC Pin 26).
- **Consum**: Tres LEDs controlats per transistors (PWM 1kHz) actuant com interruptors de banda baixa (*low-side*).
  - **Roig**: Càrrega Crítica (Pin 2).
  - **Blau**: Càrrega No Crítica (Pin 4).
  - **Verd**: Càrrega No Crítica + Safety Sink (Pin 5).
- **Emmagatzematge**: Condensador de 4700$\mu$F per absorbir transitoris.

### 2. Filtratge de Senyal
Per garantir l'estabilitat del control davant el soroll de commutació del PWM, el firmware implementa un **filtre de mediana**: es realitzen 15 mostres de l'ADC, s'ordenen i s'escull el valor central, eliminant així pics de corrent puntuals.

---

## Lògica de Treball i Modes

El SCADA tanca el llaç de control cada **50ms (20Hz)** seguint aquesta seqüència:

### Modes de Funcionament
1.  **Simulació Pura (`simulation.py`)**: Útil per validar la física i el model matemàtic d'Euler sense necessitat de maquinari.
2.  **Mode Híbrid / HIL (`hybrid.py`)**: El PC calcula la tensió del bus i l'envia a l'ESP32 via DAC. L'ESP32 la llegeix via ADC i la torna al PC. Permet testar la latència sèrie i l'error de quantificació de 12 bits.
3.  **Hardware Real (`main.py`)**: Operació sobre la micro-xarxa elèctrica real. Totes les lectures provenen dels sensors físics.

### Estratègies de Gestió (The Brain)
- **Load Shedding**: Si la tensió del bus cau, es desconnecten càrregues:
  - **V < 38V**: Es talla el LED Verd.
  - **V < 36V**: Es talla el LED Blau.
  - **LED Vermell**: Es manté sempre que sigui possible.
- **Suport de Xarxa**: Si $V_{bus} < 35V$, s'activa un control proporcional sobre la font de xarxa per injectar energia i mantenir el bus operatiu.
- **Safety Sink**: Si la tensió puja per sobre de **45V** (excedent solar sense demanda), el sistema força el LED verd al 100% de consum per dissipar energia i protegir el condensador.

---

## Com executar-lo

1.  **Preparació ESP32**:
    - Connecta l'ESP32 al PC.
    - Carrega el firmware `uControl_0.py` (MicroPython).
2.  **Maquinari**: Assegura't que el muntatge segueix el mapeig de pins definit.
3.  **Software**:
    ```bash
    # Instal·la dependències
    pip install PyQt5 pyqtgraph pyserial

    # Executa el SCADA real
    python main.py
    ```

---

## Monitorització en Temps Real

El dashboard de control inclou:
- **Balanç de Potències**: Gràfics dinàmics de generació (Solar/Grid) vs Consum.
- **Estat del Bus**: Monitorització del voltatge i de l'Estat de Càrrega (SoC) del condensador.
- **Monitor de Hardware**: Visualització de les tensions reals als pins de l'ESP32 per diagnòstic de baix nivell.

---

## Autors
*   **Arnau Coronado**
*   **Guillem Castillo**

*Projecte realitzat per a l'assignatura PGE3, EEBE (UPC).*