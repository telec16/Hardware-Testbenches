import pathlib, sys

sys.path.append(str(pathlib.Path('../_libs/').resolve()))

from VISA.VISA_controller import VisaController
from VISA.MODEL_2410 import MODEL2410
from VISA.DS4024 import DS4024

from ArduinoCarac import ArduinoCarac
from diode_test_and_save import diode_test_and_save

import time as tme
from collections import namedtuple
from string import Template
import csv


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
inst = vc.get_instruments_by_name(MODEL2410.NAME)[0]
k2410 = MODEL2410(inst)
inst = vc.get_instruments_by_name(DS4024.NAME)[0]
scope = DS4024(inst)
inst = vc.get_instruments_by_name(ArduinoCarac.NAME)[0]
arduino = ArduinoCarac(inst)
Boards = ArduinoCarac.Boards
surge = vc.get_unchecked_resource("ASRL13::INSTR")

# ################ #
# Name conventions #
# ################ #
PATH = pathlib.Path("./csv")

DIODE_LIST = [
    [Boards.B2, 'D16'],
    [Boards.A2, 'D10'],
    [Boards.A4, 'D4']]

COLUMNS = ['Timestamp_rel (ms)', 'Current (A)', 'Voltage (V)']

NameParams = namedtuple("NameParams", ["dirname", "filename"])
SURGE_NAMES = NameParams(dirname="Surge",
                         filename='''${name}_surge_${amp}A_${temp}C.csv''')
DIRECT_NAMES = NameParams(dirname="Direct",
                          filename='''${name}_direct_after-${amp}A_${temp}C.csv''')
REVERSE_NAMES = NameParams(dirname="Reverse",
                           filename='''${name}_reverse_after-${amp}A_${temp}C.csv''')

# ########### #
# Test values #
# ########### #

TEMPERATURE = 175  # Celsius

SHUNT = .004998  # Ohms

SurgeParams = namedtuple("SurgeParams", ["max_current", "step_current", "max_voltage", "scale_factor", "delay"])
SURGE_PARAMS = SurgeParams(max_current=170,  # Amps
                           step_current=10,  # Amps
                           max_voltage=25,  # Volts
                           scale_factor=1,  # N/Amps
                           delay=2)  # Secs

IVParams = namedtuple("IVParams", ["max_voltage", "step_voltage", "current_compliance"])
DIRECT_PARAMS = IVParams(max_voltage=1,  # Volts
                         step_voltage=10e-3,  # Volts
                         current_compliance=100e-3)  # Amps

REVERSE_PARAMS = IVParams(max_voltage=-1100,  # Volts
                          step_voltage=10,  # Volts
                          current_compliance=100e-6)  # Amps

do_IV_each_time = False

SCOPE_TIMEOUT = 5  # Secs

# ##### #
# Setup #
# ##### #

Diode = namedtuple("Diode", ['board', 'name', 'cycles'])
TestData = namedtuple("TestData", ['name', 'amp', 'temp'])

DIODES = []
for diode in DIODE_LIST:
    DIODES.append(Diode(*diode, 0))

    diode_dirpath = PATH / DIODES[-1].name
    (diode_dirpath / SURGE_NAMES.dirname).mkdir(parents=True, exist_ok=True)
    (diode_dirpath / DIRECT_NAMES.dirname).mkdir(parents=True, exist_ok=True)
    (diode_dirpath / REVERSE_NAMES.dirname).mkdir(parents=True, exist_ok=True)

# ######## #
# Main App #
# ######## #

arduino.orange(True)

# ################# #
# Instruments setup #
# ################# #

# k2410.melody([(440, .5), (300, .25), (350, .25), (440, .5), (500, .75)])

#  # Scope channels #  #
scope.chn_display(scope.Channels.CHANNEL1, True)
scope.chn_display(scope.Channels.CHANNEL2, True)
scope.chn_display(scope.Channels.CHANNEL3, False)
scope.chn_display(scope.Channels.CHANNEL4, False)

#  # Channels ratio #  #
scope.set_chn_ratio(scope.Channels.CHANNEL1, scope.Ratios.X1)
scope.set_chn_ratio(scope.Channels.CHANNEL2, scope.Ratios.X100)

#  # Channels invert #  #
scope.chn_invert(scope.Channels.CHANNEL1, True)
scope.chn_invert(scope.Channels.CHANNEL2, True)

#  # Time scale #  #
scope.time_scale = 20e-3 / 14  # 14 divs on this screen !
scope.time_offset = 0  # -(10e-3 / 12) * 4

#  # Trigger #  #
scope.source = scope.Channels.CHANNEL1  # Trig on current
scope.edge = scope.Slopes.NEGATIVE  # Because channel is inverted (?) -> Nope, why doesn't he want to trig correctly ??

#  # 2410 in v-source mode, output mode ZERO #  #
k2410.output_mode = k2410.OutputModes.ZERO
k2410.text1_dis = False
k2410.text2_dis = False

try:
    # ##### #
    # Start #
    # ##### #
    arduino.red(True)
    k2410.key_press = k2410.Keys.I_MEAS
    k2410.key_press = k2410.Keys.LOCAL
    for diode in DIODES:
        print("+Diode ", diode.name)

        is_dead = False
        for surge_current in range(0, SURGE_PARAMS.max_current + 1, SURGE_PARAMS.step_current):
            # ################# #
            # Instruments setup #
            # ################# #
            print("\t", surge_current, "A")
            print("\t\tSetup")

            test_datas = TestData(name=diode.name, amp=surge_current, temp=TEMPERATURE)

            #  # Surge setup #  #
            bin_current = max(0, min(255, round(surge_current * SURGE_PARAMS.scale_factor)))
            surge.write_raw(f"a{bin_current}A")
            tme.sleep(.2)
            print("\t\tans:", surge.read().strip())

            if surge_current > 0:
                #  # Channels scale #  #
                scope.set_chn_scale(scope.Channels.CHANNEL1, (surge_current * SHUNT) / 6)
                scope.set_chn_scale(scope.Channels.CHANNEL2, SURGE_PARAMS.max_voltage / 6)
                scope.set_chn_offset(scope.Channels.CHANNEL1, -(surge_current * SHUNT) / 2)
                scope.set_chn_offset(scope.Channels.CHANNEL2, -SURGE_PARAMS.max_voltage / 2)

                #  # Trigger #  #
                scope.level = surge_current * SHUNT / 2
                scope.edge = scope.Slopes.POSITIVE

                # ########### #
                # Acquisition #
                # ########### #
                print("\t\tAcquisition")

                #   # Start scope in SINGLE mode and pulse ! #  #
                scope.running = True
                scope.sweep = scope.Sweeps.SINGLE
                tme.sleep(.5)
                surge.write_raw(f"s")
                tme.sleep(.2)
                print("\t\tans:", surge.read().strip())

                #   # Wait until acquired #  #
                ts = tme.time()
                while not scope.stopped and not is_dead:
                    if (ts + SCOPE_TIMEOUT) < tme.time():
                        is_dead = True

                if not is_dead:
                    #   # Retrieve data #  #
                    time, volt = scope.get_curve(scope.Channels.CHANNEL2)
                    _, current = scope.get_curve(scope.Channels.CHANNEL1, custom_scale=1 / SHUNT)
                    time, volt, current = resize(time, volt, current)

                    cycles = diode.cycles + 1

                    # ###### #
                    # Saving #
                    # ###### #
                    print("\t\tSaving")

                    filename = Template(SURGE_NAMES.filename).safe_substitute(test_datas._asdict())
                    full_path = PATH / diode.name / SURGE_NAMES.dirname / filename

                    rows = [[time[i], current[i], volt[i]] for i in range(len(time))]

                    with open(str(full_path.resolve()), 'w', newline='') as csv_file:
                        writer = csv.writer(csv_file, dialect='excel', delimiter=',')
                        writer.writerow(COLUMNS)
                        writer.writerows(rows)

                    tme.sleep(SURGE_PARAMS.delay)

            if do_IV_each_time or surge_current == 0 or surge_current == SURGE_PARAMS.max_current:
                # ################### #
                # IV characterization #
                # ################### #

                print("\t\tDoing IV")
                delay = arduino.measure(diode.board)
                tme.sleep(delay + .5)

                print("\t\t\tDirect")
                diode_test_and_save(k2410, diode, DIRECT_PARAMS, DIRECT_NAMES, COLUMNS, PATH, test_datas)
                tme.sleep(1)
                print("\t\t\tInverse")
                diode_test_and_save(k2410, diode, REVERSE_PARAMS, REVERSE_NAMES, COLUMNS, PATH, test_datas)

                delay = arduino.surge(diode.board)
                tme.sleep(delay + .5)

            if is_dead:
                break

        print("-Diode ", diode.name)

    print("End")

    k2410.output = False
    arduino.red(False)

except Exception as e:
    k2410.output = False
    arduino.red(True)
    arduino.orange(False)
    arduino.stop()
    print(e)
except KeyboardInterrupt as e:
    k2410.output = False
    arduino.red(False)
    arduino.orange(True)
    arduino.stop()
else:
    k2410.output = False
    arduino.red(False)
    arduino.orange(False)
    arduino.stop()

try:
    del surge
    del arduino
    del scope
    del k2410

    del vc
except Exception as e:
    print("Error durring closure :")
    print(e)
