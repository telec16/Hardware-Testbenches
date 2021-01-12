import pathlib, sys

sys.path.append(str(pathlib.Path('../_libs/').resolve()))

from VISA.VISA_controller import VisaController
from VISA.PICOAMMETER import PICOAMMETER
from VISA.ArduinoAlim import ArduinoAlim

from ArduinoHTRB import ArduinoHTRB

import time as tme
from collections import namedtuple

#   # VISA controller, only one #   #
vc = VisaController(query='?*::INSTR', verbose=True)

#   # Various devices, as many as needed (but only one object for one real device) #   #
#inst = vc.get_instruments_by_name(ArduinoAlim.NAME)[0]
#alim = ArduinoAlim(inst)
inst = vc.get_instruments_by_name(ArduinoHTRB.NAME)[0]
arduino = ArduinoHTRB(inst)
Diodes = ArduinoHTRB.Device

DIODE_LIST = [
    [Diodes.B1, 'B1_87']]

Diode = namedtuple("Diode", ['board', 'name', 'isDead', 'maxCurrent', 'minCurrent', 'lastCurrent', 'cycles'])

DIODES = []
for diode in DIODE_LIST:
    DIODES.append(Diode(*diode, False, -1, 1, 0, 0))

for diode in DIODES:
    delay = arduino.enable(diode.board, True)
    tme.sleep(delay + .5)

for diode in DIODES:
    print("Measure relay On")
    delay = arduino.measure(diode.board, True)
    tme.sleep(delay + 5)
    print("Measure relay Off")
    delay = arduino.measure(diode.board, False)
    tme.sleep(delay + 5)
    

    