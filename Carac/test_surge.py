import csv
import pathlib, sys

sys.path.append(str(pathlib.Path('../_libs/').resolve()))

from VISA.VISA_controller import VisaController
from VISA.DS4024 import DS4024
from VISA.DG4062 import DG4062

from ArduinoCarac import ArduinoCarac

import time as tme


# Put all arrays to the size of the smaller one
def resize(*args: list):
    size = min(*[len(arg) for arg in args])
    r_args = [arg[0:size] for arg in args]
    return tuple(r_args)


# ########## #
# VISA stuff #
# ########## #

#   # VISA controller, only one #   #
vc = VisaController(query='?*::INSTR', verbose=True)
#   # Various devices, as many as needed (but only one object for one real device) #   #
inst = vc.get_instruments_by_name(DS4024.NAME)[0]
scope = DS4024(inst)
inst = vc.get_instruments_by_name(DG4062.NAME)[0]
fawg = DG4062(inst)
inst = vc.get_instruments_by_name(ArduinoCarac.NAME)[0]
arduino = ArduinoCarac(inst)

CHN1 = DG4062.Channels.OUT1
COLUMNS = ['Timestamp_rel (ms)', 'Current (A)', 'Voltage (V)', 'Command (V)']
PATH = pathlib.Path("./test_surge")

SHUNT = .004998
MAX_VOLTAGE = 20
RATIO = 200/3

PW = 300e-6
PULSES = [x / 2 for x in range(1, 8)]
LOW_LEVEL = -10e-3

PATH.mkdir(parents=True, exist_ok=True)

# Generator setup
fawg.set_chn_shape(CHN1, DG4062.Shapes.PULSE)
fawg.set_chn_period(CHN1, 500e-6)
fawg.set_chn_pulse_width(CHN1, 300e-6)
fawg.chn_burst(CHN1, True)
fawg.beep()

# Scope setup
#  # Scope channels #  #
scope.chn_display(scope.Channels.CHANNEL1, True)
scope.chn_display(scope.Channels.CHANNEL2, True)
scope.chn_display(scope.Channels.CHANNEL3, True)
scope.chn_display(scope.Channels.CHANNEL4, False)

#  # Channels ratio #  #
scope.set_chn_ratio(scope.Channels.CHANNEL1, scope.Ratios.X1)
scope.set_chn_ratio(scope.Channels.CHANNEL2, scope.Ratios.X100)
scope.set_chn_ratio(scope.Channels.CHANNEL3, scope.Ratios.X1)

#  # Channels invert #  #
scope.chn_invert(scope.Channels.CHANNEL1, True)
scope.chn_invert(scope.Channels.CHANNEL2, True)
scope.chn_invert(scope.Channels.CHANNEL3, False)

#  # Time scale #  #
scope.time_scale = PW / 12  # 14 divs on this screen !
scope.time_offset = (PW / 12) * 6

#  # Trigger #  #
scope.source = scope.Channels.CHANNEL3  # Trig on pulse
scope.edge = scope.Slopes.POSITIVE

input("Please enable surge")
fawg.out1 = True

arduino.relay_mux(arduino.Channels.SURGE)

for p in PULSES:
    pulse_current = p*RATIO

    #  # Channels scale #  #
    scope.set_chn_scale(scope.Channels.CHANNEL1, (pulse_current * SHUNT) / 6)
    scope.set_chn_scale(scope.Channels.CHANNEL2, MAX_VOLTAGE / 6)
    scope.set_chn_scale(scope.Channels.CHANNEL3, p / 6)
    scope.set_chn_offset(scope.Channels.CHANNEL1, -(pulse_current * SHUNT) / 2)
    scope.set_chn_offset(scope.Channels.CHANNEL2, -MAX_VOLTAGE / 2)
    scope.set_chn_offset(scope.Channels.CHANNEL3, -p / 2)

    #  # Trigger #  #
    scope.level = p / 2

    fawg.set_chn_hi_lo(CHN1, p, LOW_LEVEL)

    #   # Start scope in SINGLE mode and pulse ! #  #
    scope.running = True
    scope.sweep = scope.Sweeps.SINGLE
    tme.sleep(.5)
    fawg.chn_burst_trig(CHN1)

    #   # Wait until acquired #  #
    ts = tme.time()
    is_dead = False
    while not scope.stopped and not is_dead:
        if (ts + 5) < tme.time():
            is_dead = True

    if not is_dead:
        #   # Retrieve data #  #
        time, volt = scope.get_curve(scope.Channels.CHANNEL2)
        _, current = scope.get_curve(scope.Channels.CHANNEL1, custom_scale=1 / SHUNT)
        _, cmd = scope.get_curve(scope.Channels.CHANNEL3)
        time, volt, current, cmd = resize(time, volt, current, cmd)

        rows = [[time[i] * 1e6, current[i], volt[i], cmd[i]] for i in range(len(time))]
        filename = f"pulsed_{int(PW*1e6)}us_{p:.3}V_{int(pulse_current)}A.csv"
        full_path = PATH / filename

        with open(str(full_path.resolve()), 'w', newline='') as csv_file:
            writer = csv.writer(csv_file, dialect='excel', delimiter=',')
            writer.writerow(COLUMNS)
            writer.writerows(rows)

    fawg.beep()
    tme.sleep(1)

arduino.relay_mux(arduino.Channels.NONE)

input("Please disable surge")
fawg.out1 = False

try:
    del arduino
    del scope
    del fawg

    del vc
except Exception as e:
    print("Error during closure :")
    print(e)
