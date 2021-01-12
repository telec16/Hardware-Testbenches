import pathlib, sys

sys.path.append(str(pathlib.Path('../_libs/').resolve()))

from VISA.VISA_controller import VisaController
from VISA.MODEL_2410 import MODEL2410
from VISA.DS4024 import DS4024

from Utils.logger import Logger
from Utils.mail import simple_mail_sender

from ArduinoCarac import ArduinoCarac
from diode_test_and_save import diode_iv_and_save, diode_save
from GUI import diode_map

import time as tme
from collections import namedtuple
import traceback


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
    (Boards.B1, 'KE12DJ08L_D10'), (Boards.A1, 'KE12DJ08_D2'),
    (Boards.B2, 'KE12DJ08L_D18'), (Boards.A2, 'KE12DJ08_D4'),
    (Boards.B3, 'KE12DJ08L_D69'), (Boards.A3, 'KE12DJ08_D6'),
    (Boards.B4, 'KE12DJ08L_D37'), (Boards.A4, 'KE12DJ08_D8'),
    (Boards.B5, 'KE12DJ08L_D48'), (Boards.A5, 'KE12DJ08_D10')]
DIODE_MAP = diode_map(DIODE_LIST)

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

TEMPERATURE = 25  # Celsius

SHUNT = .004998  # Ohms

SurgeParams = namedtuple("SurgeParams", ["max_current", "step_current", "max_voltage", "scale_factor", "delay"])
SURGE_PARAMS = SurgeParams(max_current=200,  # Amps
                           step_current=10,  # Amps
                           max_voltage=15,  # Volts
                           scale_factor=1,  # N/Amps
                           delay=2)  # Secs

IVParams = namedtuple("IVParams", ["max_voltage", "step_voltage", "current_compliance"])
# 50 sec
DIRECT_PARAMS = IVParams(max_voltage=1,  # Volts
                         step_voltage=10e-3,  # Volts
                         current_compliance=100e-3)  # Amps

# 30 sec
REVERSE_PARAMS = IVParams(max_voltage=-1100,  # Volts
                          step_voltage=10,  # Volts
                          current_compliance=100e-6)  # Amps

do_IV_each_time = True

SCOPE_TIMEOUT = 5  # Secs

# ##### #
# Setup #
# ##### #

logger = Logger(logger_id="Carac", time_format="%d/%m/%y %H:%M:%S", path=pathlib.Path('./log'), default_save=True)

Diode = namedtuple("Diode", ['board', 'name'])
TestData = namedtuple("TestData", ['name', 'amp', 'temp'])

DIODES = []
for diode in DIODE_LIST:
    DIODES.append(Diode(*diode))

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
scope.edge = scope.Slopes.NEGATIVE  # Because channel is inverted

#  # 2410 in v-source mode, output mode ZERO #  #
k2410.output_mode = k2410.OutputModes.ZERO
k2410.text1_dis = False
k2410.text2_dis = False

logger.log(0, f"Will test :")
logger.log(1, f"{DIODE_MAP}")
logger.log(0, f"")
try:
    # ##### #
    # Start #
    # ##### #
    arduino.red(True)
    k2410.key_press = k2410.Keys.I_MEAS
    k2410.key_press = k2410.Keys.LOCAL

    first_time = True

    for diode in DIODES:
        logger.log(0, f"+Diode {diode.name}")

        is_dead = False
        for surge_current in range(0, SURGE_PARAMS.max_current + 1, SURGE_PARAMS.step_current):
            # ################# #
            # Instruments setup #
            # ################# #
            logger.log(1, f"{surge_current} A")
            logger.log(2, "Setup")

            test_datas = TestData(name=diode.name, amp=surge_current, temp=TEMPERATURE)

            #  # Surge setup #  #
            bin_current = max(0, min(255, round(surge_current * SURGE_PARAMS.scale_factor)))
            surge.write_raw(f"a{bin_current}A")
            tme.sleep(.2)
            logger.log(2, f"ans: {surge.read().strip()}")

            if surge_current > 0:
                #  # Channels scale #  #
                scope.set_chn_scale(scope.Channels.CHANNEL1, (surge_current * SHUNT) / 6)
                scope.set_chn_scale(scope.Channels.CHANNEL2, SURGE_PARAMS.max_voltage / 6)
                scope.set_chn_offset(scope.Channels.CHANNEL1, -(surge_current * SHUNT) / 2)
                scope.set_chn_offset(scope.Channels.CHANNEL2, -SURGE_PARAMS.max_voltage / 2)

                #  # Trigger #  #
                scope.level = surge_current * SHUNT / 2

                # ########### #
                # Acquisition #
                # ########### #
                logger.log(2, "Acquisition")

                # The first time, two pulses are played to initialize the surge controller
                for _ in range(2 if first_time else 1):
                    #   # Start scope in SINGLE mode and pulse ! #  #
                    scope.running = True
                    scope.sweep = scope.Sweeps.SINGLE
                    tme.sleep(.5)
                    surge.write_raw(f"s")
                    tme.sleep(.2)
                    logger.log(2, f"ans: {surge.read().strip()}")

                    #   # Wait until acquired #  #
                    ts = tme.time()
                    while not scope.stopped and not is_dead:
                        if (ts + SCOPE_TIMEOUT) < tme.time():
                            is_dead = True

                    tme.sleep(SURGE_PARAMS.delay)

                first_time = False

                if not is_dead:
                    #   # Retrieve data #  #
                    time, volt = scope.get_curve(scope.Channels.CHANNEL2)
                    _, current = scope.get_curve(scope.Channels.CHANNEL1, custom_scale=1 / SHUNT)
                    time, volt, current = resize(time, volt, current)

                    # ###### #
                    # Saving #
                    # ###### #
                    logger.log(2, "Saving")
                    rows = [[time[i] * 1e3, current[i], volt[i]] for i in range(len(time))]
                    diode_save(COLUMNS, rows, PATH, SURGE_NAMES, test_datas)

            do_IV = is_dead or surge_current == 0 or surge_current == SURGE_PARAMS.max_current
            if do_IV_each_time or do_IV:
                # ################### #
                # IV characterization #
                # ################### #

                logger.log(2, "Doing IV")
                delay = arduino.measure(diode.board)
                tme.sleep(delay + .5)

                logger.log(3, "Direct")
                diode_iv_and_save(k2410, DIRECT_PARAMS, COLUMNS, PATH, DIRECT_NAMES, test_datas, autoscale=True)
                tme.sleep(1)
                logger.log(3, "Inverse")
                diode_iv_and_save(k2410, REVERSE_PARAMS, COLUMNS, PATH, REVERSE_NAMES, test_datas)

                delay = arduino.surge(diode.board)
                tme.sleep(delay + .5)

            if is_dead:
                break

        logger.log(0, f"-Diode {diode.name}")

    logger.log(0, "End")

    k2410.output = False
    arduino.red(False)

except Exception as e:
    k2410.output = False
    arduino.red(True)
    arduino.orange(False)
    arduino.stop()

    # Logging
    traceback.print_exc()
    log_str = f"Error : {str(e)}" \
              f"Traceback :" \
              f"{traceback.format_exc()}"
    logger.log(0, log_str)
    simple_mail_sender(["calytechnologies+surge@gmail.com",
                        "loup.plantevin@insa-lyon.fr",
                        "d.tournier@caly-technologies.com",
                        "j.fonder@caly-technologies.com"],
                       "Surge Panic !", log_str)
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
    logger.log(0, "Error during closure :")
    logger.log(0, str(e))
    traceback.print_exc()

logger.log(0, "Test terminated")
simple_mail_sender(["calytechnologies+surge@gmail.com",
                    "loup.plantevin@insa-lyon.fr",
                    "d.tournier@caly-technologies.com",
                    "j.fonder@caly-technologies.com"],
                   "Surge ended", f"Test terminated\nSuccess ?\n{DIODE_MAP}")
