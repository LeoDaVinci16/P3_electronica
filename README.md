# Sistema SCADA de Control de Micro-xarxa (Simulació + Hardware)

Aquest projecte implementa un sistema de gestió energètica per a una micro-xarxa DC, combinant un motor de simulació física amb una implementació real mitjançant un microcontrolador ESP32. El sistema permet monitoritzar el balanç de potències, gestionar càrregues crítiques i controlar l'emmagatzematge d'energia.

## 📂 Estructura del Projecte

El programari està dividit en mòduls independents per facilitar el manteniment i permetre l'execució en mode simulat o real:

```text
P3/
├── main.py              # Orquestrador principal per a l'ús amb Hardware Real.
├── simulation.py        # Orquestrador per a l'execució en mode Simulació Pura.
├── brain.py             # Cervell del sistema: lògica de control i escalat de dades.
├── gui.py               # Gestió de les finestres gràfiques i interfície PyQt5.
├── control_esp32.py     # Driver de comunicació sèrie (DAC/ADC) amb l'ESP32.
├── ui.py                # Classe d'interfície generada a partir de QtDesigner.
├── irradiancia.csv      # Base de dades solar hora a hora (Barcelona).
└── uControl_0.py        # Codi MicroPython per instal·lar a l'ESP32.
```

## ⚡ Especificacions de la Micro-xarxa

El sistema simula i controla un bus de corrent continu amb els següents paràmetres:

*   **Tensió Nominal del Bus:** 40 V.
*   **Tensió Màxima de Seguretat:** 50 V.
*   **Emmagatzematge:** Condensador electrolític de 12.000 µF (12 mF).
*   **Generació FV:** Basada en dades reals del PVGiS (Barcelona), escalada a 1000W pic.
*   **Generació de Xarxa:** Font de suport externa capaç d'injectar potència si la bateria s'exhaureix.
*   **Càrregues:** 
    *   **Càrrega 1 (Roig):** Crítica (mai es desconnecta voluntàriament).
    *   **Càrrega 2 (Blau) i 3 (Verd):** No crítiques (gestionades pel sistema).

## 🧠 Lògica de Control

La presa de decisions es realitza dins de `brain.py` seguint aquests criteris:

### 1. Gestió de Càrregues (Load Shedding)
Per garantir l'estabilitat del sistema i la supervivència de la càrrega crítica:
*   Si la tensió del bus **cau per sota de 30V**, el sistema desconnecta automàticament les càrregues **Blava i Verda**. Els seus lliscadors a la interfície tornen a la posició 0 per avisar l'usuari.

### 2. Suport de Xarxa Elèctrica
*   La xarxa només consumeix energia per injectar-la al bus (importació).
*   **Mode Manual:** L'usuari tria quina potència importar amb el lliscador vertical (0-2550W).
*   **Mode Automàtic:** Si el bus baixa dels **30V** i la càrrega crítica està activa, la xarxa injecta potència addicional proporcional a l'error de tensió per mantenir el bus estable.

### 3. Estat de Càrrega (SoC)
En tractar-se d'un condensador, l'estat de càrrega es modela de forma lineal respecte al voltatge:
*   **0% SoC:** 0 V.
*   **100% SoC:** 50 V.
*   *Nota:* El sistema treballa normalment entre el 60% (30V) i el 80% (40V).

## 🖥️ Funcionament de l'SCADA (GUI)

L'aplicació obre diverses finestres per a una monitorització completa:

1.  **Finestra de Control:** Interfície principal amb els lliscadors de consum i xarxa, i marcadors LCD de potències (W), corrents (A) i voltatges (V).
2.  **Monitorització en Temps Real:** Un mosaic 2x2 amb:
    *   **Tensió del Bus:** Comparativa entre el valor Simulat (groc) i el Real (magenta).
    *   **SoC:** Evolució del percentatge d'energia emmagatzemada.
    *   **Balanç de Potències:** Corbes de Solar, Xarxa, Consum i potència neta al condensador.
    *   **Intensitats:** Visualització de la KCL (Llei de Kirchhoff) on es veu que la suma de corrents és zero.
3.  **Monitor de l'ESP32 (Només Hardware):** Gràfiques de baix nivell que mostren els volts reals (0-3.3V) als pins físics DAC 25, DAC 26 i ADC 34.

## 🚀 Execució

### Mode Simulació Pura
Ideal per provar la lògica a casa sense necessitat de tenir l'ESP32 connectat. Utilitza un model físic iteratiu (aproximació d'Euler) per calcular la tensió del condensador.

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