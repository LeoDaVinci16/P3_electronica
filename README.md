# Sistema SCADA control de càrregues
**Guillem Castillo i Arnau Coronado**

Aquest projecte implementa una interfície SCADA (Supervisory Control and Data Acquisition) en temps real per gestionar un sistema energètic híbrid que consta de generació fotovoltaica (FV), una conexió a la xarxa i múltiples càrregues de consum.

El sistema està dissenyat per monitoritzar el balanç energètic i assegurar que la càrrega crítica sempre estigui alimentada mitjançant la regulació automàtica del generador de reserva.

El simulador, un cop inicialitzat el programa control_v3.py obre dues pestanyes. En la primera és el control SCADA del sistema simulat, mentre l’altra és una interfície que mostra l’evolució gràfica de diversos paràmetres del sistema.


## 🚀 SCADA

### Potencia d'entrada
A la part superior esquerra de la interfície gràfica hi ha el requadre de potencia d’entrada. En aquest requadre hi ha els següents elements:
- Dos marcadors que mostren la **quantitat d’energia generada**. Pot ser d’origen solar i l’energia injectada des de la xarxa elèctrica en Watts. L’energia solar és determinada per un arxiu d’irradiàncies anual hora a hora a la localitat de Barcelona, extret del PVGiS. L’energia aportada per la xarxa es controla amb un control  proporcional que mou automaticament l’slider que hi ha al costat del marcador.
- Just a sota hi ha un marcador on mostra la potència global total disponible solar + xarxa.

### Potencia consumida
A la part superior dreta hi ha el requadre d’energia consumida. Dins d’aquest hi ha els següents elements:

- Tres sliders, que són els que permeten controlar manualment les tres càrregues i uns indicadors que mostren el valor, en Ampers, del corrent que circula per les càrregues. 
    - Roig: Carrega crítica. Si no hi ha suficient potencia generada, s'utilitza la xarxa per subministrar-la.
    - Blau: Càrrega no crítica, si no hi ha suficient potencia es desconecta automaticament.
    - Verd: Càrrega no crítica, càrrega no crítica, si no hi ha suficient potencia es desconecta automaticament.
- Un marcador la potència que es consumeix sumant el consum de totes les tres càrregues. Està situat sota els 3 sliders.

### Emmagatzematge
A la part central hi ha el requadre  “Emmagatzematge” dins d’aquest hi ha els següents elements:
- Marcador de la tensió del bus.
- Marcador de l’estat de càrrega (SoC) del condensador.
- Marcador amb la potència entregada o subministrada pel condensador.

### Esquema
A la part inferior  hi ha el requadre “Esquema”, que mostra un esquema del circuit simulat. S'hi recullen les següents magnituds:

- La tensió de bus del circuit (tensió al condensador).
- Corrent a cada branca:
    - Corrent fotovoltaica generada
    - Corrent extreta de la xarxa
    - Corrent subministrada o consumida pel condensador.
    - Corrent consumida per cadascuna de les càrregues.

### Simulació

Finalment hi ha un requadre amb el temps de simulació, la data (a partir de les dades d'irradiancia fotovoltaica) i el botó "exit" serveix per tancar la finestra de l'SCADA i la dels gràfics en un sol clic.

## Gràfics en temps real

- **Gràfics en temps real**: Visualitza el balanç energètic net (Generació - Consum) utilitzant `pyqtgraph`.


## 🛠️ Estructura del projecte

- `control.py`: La lògica principal de l'aplicació i la gestió de la GUI.
- `ui.py`: Classe Python generada a partir del fitxer `.ui` de Qt Designer.
- `ui.ui`: El fitxer de disseny original per a Qt Designer.
- `irradiancia.csv`: Fitxer amb les dades d'irradiancia obtingudes amb PVGiS
- `requeriments.txt`: Paquets necessaris per executar el programa
- `dibuix_rc.py`, `dibuix.qrc` i `circuit.png`: Fitxers per integrar la imatge de l'esquema del circuit a la interfície d'usuari.
- `README.md`: Aquest document

## 📋 Requisits previs

Assegureu-vos de tenir Python 3.x instal·lat. També necessitareu les següents llibreries:

```bash
pip install PyQt5 pyqtgraph pyserial
```

## ⚙️ Instalació i us

### 1. Compilació de la UI
Si modifiques l'arxiu `ui.ui` amb el Qt Designer, has de regenerar la classe Python:
```bash
pyrcc5 dibuix.qrc -o dibuix_rc.py
pyuic5 ui_v1.ui -o control_ui_v1.py
```

### 2. Executar la simulació
Per iniciar la interfície SCADA:

```bash
python control_v1.py
```

### 3. Configuració del maquinari (opcional)
Si feu servir un ESP32:
1. Instal·leu `uControl.py` al vostre ESP32 amb Thonny o rshell.
2. Connecteu l'ESP32 mitjançant USB.
3. Assegureu-vos que `USE_SERIAL` estigui definit com a `True` a la configuració (si escau).

---
*Desenvolupat com a part del Màster en Enginyeria Electrònica (P3 Electrònica).*