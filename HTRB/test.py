import pathlib, sys

sys.path.append(str(pathlib.Path('../_libs/').resolve()))

from VISA.VISA_controller import VisaController
from VISA.MODEL_2410 import MODEL2410
from VISA.PICOAMMETER import PICOAMMETER

from ArduinoHTRB import ArduinoHTRB
import time

vc = VisaController(query='?*::INSTR', verbose=True)
inst = vc.get_instruments_by_name(ArduinoHTRB.NAME)[0]
arduino = ArduinoHTRB(inst)
Diodes = ArduinoHTRB.Device

diodes = [
Diodes.B1,
Diodes.B2,
Diodes.B3,
Diodes.B4,
Diodes.B5,
Diodes.B6,
Diodes.B7,
Diodes.B8]

relays = [arduino.relay_on, arduino.relay_gnd, arduino.relay_mes]


state=False
while True:
    for relay in relays:
        for diode in diodes:
            relay(diode, state)
            time.sleep(.2)
        time.sleep(1)
    time.sleep(2)
    state=not state