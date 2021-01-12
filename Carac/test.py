import pathlib, sys

sys.path.append(str(pathlib.Path('../_libs/').resolve()))

from VISA.VISA_controller import VisaController
from VISA.MODEL_2410 import MODEL2410
from VISA.PICOAMMETER import PICOAMMETER

from ArduinoCarac import ArduinoCarac
import time

vc = VisaController(query='?*::INSTR', verbose=True)
inst = vc.get_instruments_by_name(ArduinoCarac.NAME)[0]
arduino = ArduinoCarac(inst)
Diodes = ArduinoCarac.Device

diodes = [
Diodes.B1,
Diodes.B2,
Diodes.B3,
Diodes.B4,
Diodes.B5,
Diodes.B6,
Diodes.B7,
Diodes.B8,
Diodes.B9,
Diodes.B10,
Diodes.B11,
Diodes.B12]

relays = [arduino.relay_on, arduino.relay_gnd, arduino.relay_mes]


state=True
while True:
    for relay in relays:
        for diode in diodes:
            relay(diode, state)
            time.sleep(1)
        time.sleep(1.5)
    time.sleep(2)
    state=not state