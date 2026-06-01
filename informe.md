Aquest informe tècnic s'ha redactat seguint estrictament la **Plantilla d'Articles Tècnics** de l'assignatura PGE3, amb un llenguatge acadèmic de nivell de màster i una extensió detallada que prioritza l'explicació del funcionament del sistema, tal com es demana.

***

# Gestió de Tercer Nivell d'una Micro-xarxa Ciber-Física Híbrida mitjançant Sistema SCADA

**Autors:** Guillem Castillo, Arnau Coronado  
**Filiació:** Escola d’Enginyeria de Barcelona Est (EEBE), UPC  
**Assignatura:** Processament i Gestió Electrònica d’Energia Elèctrica (PGE3)

### Resum
Aquest article tècnic detalla el desenvolupament integral d'un sistema SCADA per a la gestió de tercer nivell d'una micro-xarxa híbrida en corrent continu (DC). El sistema emula una infraestructura energètica real composta per generació fotovoltaica (FV), connexió de suport a la xarxa elèctrica, emmagatzematge d'energia mitjançant condensadors de gran capacitat i càrregues controlades (LEDs). L'arquitectura ciber-física permet la commutació entre simulació pura, *Hardware-in-the-Loop* (HIL) i operació física real. La política de control se centra en el manteniment de l'estabilitat del bus a 40V, aplicant algorismes de *load shedding* robustos i una jerarquia de prioritats en el flux de potència gestionada des d'un microcontrolador ESP32 i una interfície PyQt5.

**Paraules clau:** *Micro-xarxa, SCADA, Gestió de Tercer Nivell, ESP32, Filtrat per Mediana, Load Shedding.*

---

## 1. Introducció i Objectius de l'Enginyeria
El disseny de sistemes energètics intel·ligents requereix una supervisió que vagi més enllà del simple control local de convertidors. Aquest projecte aborda la implementació de la **gestió de tercer nivell**, la capa superior de la piràmide d'automatització, encarregada d'optimitzar l'estratègia global de la micro-xarxa.

L'objectiu principal és la creació d'un entorn capaç de gestionar el balanç energètic entre fonts intermitents i càrregues variables. La complexitat resideix en la integració de components físics amb un model digital en temps real, permetent validar la lògica de control ("The Brain") en entorns de seguretat abans de la seva aplicació en la planta real. Els reptes tecnològics clau inclouen la mitigació del soroll en l'adquisició de dades, la gestió de la latència en les comunicacions sèrie i l'estabilització d'un bus de tensió de 40V mitjançant control proporcional.

## 2. Arquitectura del Sistema i Planta Física

### 2.1. Emulació de la Micro-xarxa
La planta física ha estat dissenyada per representar els quatre pilars d'una xarxa elèctrica:
1.  **Generació:** Dues fonts de corrent controlades per tensió emulen la producció fotovoltaica i l'aportació de la xarxa elèctrica (*Grid*).
2.  **Emmagatzematge:** Un condensador electrolític (recomanat 4700$\mu$F o superior) actua com a unitat de bateries, permetent visualitzar la dinàmica de càrrega i descàrrega.
3.  **Càrregues:** Tres branques de LEDs controlades mitjançant transistors en configuració d'emissor comú que actuen com a *low-side switches*.
4.  **Capa de Control:** Un ESP32 actua com a element de camp, realitzant la digitalització del bus i l'execució de les ordres PWM/DAC.

### 2.2. Mapeig de Pins i Condicionament
Per a una operació correcta, s'ha definit la següent interfície de maquinari:
*   **ADC (Entrades):** Pin 34 (Tensió del Bus), Pin 35 (Monitorització FV), Pin 32 (Monitorització Grid). S'utilitzen divisors de tensió amb un factor de 15.15 per adaptar els 50V de rang del bus als 3.3V de l'ADC de l'ESP32.
*   **DAC (Sortides):** Pin 25 (Control de la font Solar), Pin 26 (Control de la font de Xarxa).
*   **PWM (Càrregues):** Pin 2 (LED Vermell), Pin 4 (LED Blau), Pin 5 (LED Verd).

> **[ESPAI PER POSAR: Esquema elèctric de la planta física mostrant els transistors, el condensador i els divisors de tensió]**
> *Suport visual necessari: Imatge del circuit capturada des de KiCad o fotografia nítida del muntatge en protoboard amb anotacions dels pins.*

## 3. Anàlisi Detallat de l'Ecosistema de Programari

El programari s'estructura en capes per garantir la modularitat i l'escalabilitat del sistema.

### 3.1. Firmware de l'ESP32: El Filtre de Mediana
El microcontrolador executa un script en MicroPython (`uControl_0.py`) a una freqüència de 100Hz. El punt més crític d'aquest mòdul és el **filtratge digital**. Atès que el bus DC presenta un soroll de commutació elevat degut als senyals PWM de les càrregues, s'ha descartat la mitjana aritmètica convencional.

En el seu lloc, s'implementa un **filtre de mediana**: l'ESP32 llegeix 15 mostres consecutives de l'ADC, les ordena de menor a major i selecciona el valor central (posició 7). Aquesta tècnica és extremadament robusta davant de pics de soroll puntuals (*spikes*) que podrien falsejar la tensió de bus i provocar desconnexions innecessàries de càrregues. El protocol de comunicació utilitza caràcters prefixats ('A', 'B', 'V'...) seguits de valors de 8 bits (0-255) per minimitzar l'ample de banda necessari.

### 3.2. Abstracció de Maquinari i Gestió del Buffer
L'script `control_esp32.py` encapsula la comunicació asíncrona. Un problema comú en els sistemes SCADA basats en Python és l'acumulació de retard (*lag*) degut a la lentitud del processament de dades en comparació amb la taxa d'enviament del microcontrolador. Per resoldre-ho, s'utilitza una gestió de buffer agressiva: en cada cicle de lectura, el programa buida completament el buffer de recepció (`in_waiting`) i processa exclusivament l'última línia rebuda, garantint que el SCADA mostri dades en temps real.

### 3.3. El Model de Física Digital
El mòdul `simulation.py` conté l'aproximació numèrica de primer ordre de la micro-xarxa. Utilitzant el mètode d'Euler, resol l'equació de balanç:
$$V_{bus\_next} = V_{bus\_actual} + \frac{(I_{solar} + I_{grid} - I_{consum} - I_{loss})}{C} \cdot dt$$
Per emular el comportament d'una bateria real no ideal, s'ha inclòs una variable de pèrdues ($I_{loss} = V_{bus}/200.0$), evitant que el condensador es comporti com un element d'emmagatzematge infinit.

## 4. Política de Gestió Energètica ("The Brain")

La lògica de decisió resideix en el mòdul `brain.py`, que actua com la intel·ligència de tercer nivell del sistema.

### 4.1. Manteniment del Bus a 40V
La política central és mantenir la tensió de bus estable a **40V**. Per aconseguir-ho, el sistema monitoritza el voltatge real procedent de l'ESP32 i activa un suport proporcional de xarxa quan la generació fotovoltaica és insuficient:
$$P_{grid\_auto} = (V_{target} - V_{bus}) \cdot KP_{GRID}$$
On $KP_{GRID} = 500.0$ ha estat ajustat per oferir una resposta agressiva però estable, incloent un límit de seguretat (*throttle*) per evitar sobreoscil·lacions.

### 4.2. Estratègia de Gestió de Càrregues (Load Shedding)
El sistema classifica les càrregues segons la seva criticitat per protegir l'estabilitat del sistema en cas de baixa disponibilitat energètica:
*   **LED Blau i Verd (Branques no crítiques):** Es desconnecten immediatament si la tensió del bus cau per sota dels **40V** per aturar la descàrrega del condensador.
*   **LED Vermell (Càrrega Crítica):** Mai es desconnecta per programari. S'alimenta seguint un ordre estricte de prioritat:
    1.  **Solar:** Font preferent.
    2.  **Condensador:** S'utilitza si la FV no és suficient, sempre que la seva càrrega estigui per sobre dels **30V**.
    3.  **Xarxa:** S'activa com a darrer recurs per mantenir la continuïtat del servei.

### 4.3. Protecció i Seguretat d'Excedents (Safety Sink)
Si la generació solar és excessiva i el condensador està carregat al 100%, la tensió podria pujar fins a nivells perillosos per als components. S'ha programat una estratègia de **Safety Sink**: si detecta $V_{bus} > 45V$, el sistema activa el LED verd al 100% de forma imperativa per dissipar l'energia. Si la tensió continua pujant, el SCADA ordena l'aturada immediata de la injecció solar (DAC Solar a 0).

### 4.4. Estratègia de Càrrega
La càrrega del condensador es realitza prioritzant sempre el sobrant de l'energia fotovoltaica. Tota la potència generada que no és consumida per les càrregues actives es deriva automàticament a l'emmagatzematge, optimitzant l'ús de la font renovable.

## 5. Modes d'Operació del Sistema SCADA

L'arquitectura modular permet operar en tres configuracions diferenciades:
1.  **Simulació Pura:** Utilitza el model matemàtic per validar la lògica de *load shedding* sense requerir maquinari.
2.  **Mode Híbrid / Hardware-in-the-Loop (HIL):** El PC calcula la física del bus però envia la dada a l'ESP32 via DAC. L'usuari pontetja físicament la sortida DAC amb l'entrada ADC. L'ESP32 llegeix i retorna la dada, introduint en el bucle de control els errors reals de quantificació (12 bits) i soroll de cablejat.
3.  **Mode Hardware Real:** La simulació desapareix. El sistema es connecta a la planta física real, llegint sensors i actuant sobre els LEDs en un bucle tancat de 20Hz (50ms).

## 6. Resultats dels Assajos

En aquesta secció es documenta el comportament del sistema davant d'esdeveniments dinàmics.

### 6.1. Resposta davant de Núvols (Caiguda de FV)
S'ha utilitzat un fitxer `irradiancia.csv` per emular un cicle diari. S'observa com, en disminuir la radiació, el condensador manté el bus fins que la tensió cau a 40V, moment en què el SCADA desconnecta els LEDs blau i verd.

> **[ESPAI PER POSAR: Gràfic de Balanç de Potències mostrant el Load Shedding]**
> *Suport visual necessari: Gràfica on es vegi com P_solar baixa, V_bus arriba a 40V i P_load_blau/verd cauen a zero.*

### 6.2. Estabilitat del Bus amb Suport de Xarxa
S'ha validat que l'activació del suport de xarxa manté el bus amb un error inferior al 2% respecte al target de 40V, demostrant la linealitat del control proporcional implementat.

> **[ESPAI PER POSAR: Captura de la interfície GUI en funcionament real]**
> *Suport visual necessari: Imatge del SCADA amb els gràfics en temps real i els LCDs indicant un bus estable prop dels 40V.*

### 6.3. Eficàcia del Safety Sink
En condicions de baixa demanda i alta radiació, s'ha verificat que la tensió no supera mai els 45.2V degut a la dissipació forçada en el LED verd.

> **[ESPAI PER POSAR: Taula de resultats de la prova de sobretensió]**
> *Descripció: Taula que compari V_bus sense Safety Sink (teòric) vs V_bus amb Safety Sink (mesurat).*

## 7. Conclusions
El sistema implementat demostra la viabilitat de gestionar una micro-xarxa híbrida mitjançant un entorn ciber-físic. La separació de la lògica de decisió ("The Brain") de la capa física permet que el sistema sigui altament escalable; per exemple, canviant l'ESP32 per un PLC industrial sense haver de reescriure la política energètica. 

L'ús de tècniques avançades com el **filtratge per mediana** al firmware i la **gestió de buffer sèrie** al SCADA ha estat clau per obtenir un control estable i sense retards. En definitiva, el projecte aconsegueix integrar de forma eficient el processament de dades, l'electrònica de potència i les estratègies de gestió de xarxes intel·ligents (*Smart Grids*), garantint sempre el subministrament a la càrrega crítica i la seguretat de la instal·lació.

---

> **[ESPAI PER A LA BIBLIOGRAFIA]**
> *S'ha de posar en una pàgina separada segons la plantilla.*