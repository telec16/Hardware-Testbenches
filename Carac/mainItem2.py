import pathlib, sys
import traceback

from GUI import diode_map
from Utils import Logger, simple_mail_sender

sys.path.append(str(pathlib.Path('../_libs/').resolve()))

from VISA.VISA_controller import VisaController
from VISA.MODEL_2410 import MODEL2410
from VISA.DS4024 import DS4024

from ArduinoCarac import ArduinoCarac
from diode_test_and_save import diode_iv_and_save, diode_save

import time as tme
from collections import namedtuple


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
    (Boards.B1, 'KE12DJ08L_D1'), (Boards.A1, 'KE12DJ08_D13'),
    (Boards.B2, 'KE12DJ08L_D3'), (Boards.A2, 'KE12DJ08_D15'),
    (Boards.B3, 'KE12DJ08L_D5'), (Boards.A3, 'KE12DJ08_D17'),
    (Boards.B4, 'KE12DJ08L_D7'), (Boards.A4, 'KE12DJ08_D19'),
    (Boards.B5, 'KE12DJ08L_D13'), (Boards.A5, 'KE12DJ08_D21')]
DIODE_MAP = diode_map(DIODE_LIST)

COLUMNS = ['Timestamp_rel (ms)', 'Current (A)', 'Voltage (V)']

NameParams = namedtuple("NameParams", ["dirname", "filename"])
SURGE_NAMES = NameParams(dirname="Surge",
                         filename='''${name}_surge_${amp}A_${temp}C_${repetition}.csv''')
DIRECT_NAMES = NameParams(dirname="Direct",
                          filename='''${name}_direct_after-${amp}A_${temp}C_${repetition}.csv''')
REVERSE_NAMES = NameParams(dirname="Reverse",
                           filename='''${name}_reverse_after-${amp}A_${temp}C_${repetition}.csv''')
VI_NAMES = NameParams(dirname="VI",
                      filename='''${name}_VI_after-${amp}A_${temp}C_${repetition}.csv''')

# ########### #
# Test values #
# ########### #

TEMPERATURE = 25  # Celsius

SHUNT = .004998  # Ohms

SurgeParams = namedtuple("SurgeParams",
                         ["A_current", "B_current", "max_voltage", "scale_factor", "repetition", "delay"])
SURGE_PARAMS = SurgeParams(A_current=60,  # Amps
                           B_current=60,  # Amps
                           max_voltage=10,  # Volts
                           repetition=1000,  # N
                           scale_factor=1,  # N/Amps
                           delay=2)  # Secs

IVParams = namedtuple("IVParams", ["max_voltage", "step_voltage", "current_compliance"])
IV_DIRECT_PARAMS = IVParams(max_voltage=1,  # Volts
                            step_voltage=10e-3,  # Volts
                            current_compliance=100e-3)  # Amps

IV_REVERSE_PARAMS = IVParams(max_voltage=-1100,  # Volts
                             step_voltage=10,  # Volts
                             current_compliance=100e-6)  # Amps

I_list = [10e-9, 1e-6, 100e-6]  # Amps
V_list = [-960]  # Volts

do_IV_each_time = False

SCOPE_TIMEOUT = 5  # Secs

# ##### #
# Setup #
# ##### #

logger = Logger(logger_id="Repetitive", time_format="%d/%m/%y %H:%M:%S", path=pathlib.Path('./log'), default_save=True)

Diode = namedtuple("Diode", ['board', 'name'])
TestData = namedtuple("TestData", ['name', 'amp', 'temp', 'repetition'])

DIODES = []
for diode in DIODE_LIST:
    DIODES.append(Diode(*diode))

    diode_dirpath = PATH / DIODES[-1].name
    (diode_dirpath / SURGE_NAMES.dirname).mkdir(parents=True, exist_ok=True)
    (diode_dirpath / DIRECT_NAMES.dirname).mkdir(parents=True, exist_ok=True)
    (diode_dirpath / REVERSE_NAMES.dirname).mkdir(parents=True, exist_ok=True)
    (diode_dirpath / VI_NAMES.dirname).mkdir(parents=True, exist_ok=True)

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

    for diode in DIODES:
        logger.log(0, f"+Diode {diode.name}")

        # ################# #
        # Instruments setup #
        # ################# #
        diode_side = diode.board.value[0]
        surge_current = SURGE_PARAMS.A_current if diode_side == "A" else SURGE_PARAMS.B_current

        logger.log(1, "Setup")
        logger.log(2, f"{surge_current} A")

        #  # Surge setup #  #
        bin_current = max(0, min(255, round(surge_current * SURGE_PARAMS.scale_factor)))
        surge.write_raw(f"a{bin_current}A")
        tme.sleep(.2)
        logger.log(2, f"ans: {surge.read().strip()}")

        #  # Channels scale #  #
        scope.set_chn_scale(scope.Channels.CHANNEL1, (surge_current * SHUNT) / 6)
        scope.set_chn_scale(scope.Channels.CHANNEL2, SURGE_PARAMS.max_voltage / 6)
        scope.set_chn_offset(scope.Channels.CHANNEL1, -(surge_current * SHUNT) / 2)
        scope.set_chn_offset(scope.Channels.CHANNEL2, -SURGE_PARAMS.max_voltage / 2)

        #  # Trigger #  #
        scope.level = surge_current * SHUNT / 2

        logger.log(1, "Repetitive")
        is_dead = False
        for rep in range(0, SURGE_PARAMS.repetition + 1):

            logger.log(2, f">{rep}")
            test_datas = TestData(name=diode.name, amp=surge_current, temp=TEMPERATURE, repetition=rep)

            if rep > 0:
                # ########### #
                # Acquisition #
                # ########### #
                logger.log(3, "Acquisition")

                #   # Start scope in SINGLE mode and pulse ! #  #
                scope.running = True
                scope.sweep = scope.Sweeps.SINGLE
                tme.sleep(.5)
                surge.write_raw(f"s")
                tme.sleep(.2)
                logger.log(3, f"ans: {surge.read().strip()}")

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

                    # ###### #
                    # Saving #
                    # ###### #
                    logger.log(3, "Saving")
                    rows = [[time[i]*1e3, current[i], volt[i]] for i in range(len(time))]
                    diode_save(COLUMNS, rows, PATH, SURGE_NAMES, test_datas)

                    tme.sleep(SURGE_PARAMS.delay)

            if do_IV_each_time or is_dead or rep == 0 or rep == SURGE_PARAMS.repetition:
                # ################### #
                # IV characterization #
                # ################### #

                logger.log(3, "Doing IV")
                delay = arduino.measure(diode.board)
                tme.sleep(delay + .5)

                logger.log(4, "Direct")
                diode_iv_and_save(k2410, IV_DIRECT_PARAMS, COLUMNS, PATH, DIRECT_NAMES, test_datas)
                tme.sleep(1)
                logger.log(4, "Inverse")
                diode_iv_and_save(k2410, IV_REVERSE_PARAMS, COLUMNS, PATH, REVERSE_NAMES, test_datas)

                delay = arduino.surge(diode.board)
                tme.sleep(delay + .5)

            else:
                # ######################### #
                # small IV characterization #
                # ######################### #

                logger.log(3, "Doing small IV")
                delay = arduino.relay_mes(diode.board, False)
                tme.sleep(delay + .5)
                delay = arduino.relay_mux(ArduinoCarac.Channels.MES)
                tme.sleep(delay + .5)

                logger.log(4, "I source")
                data = k2410.vi_wizard(v_compliance=-IV_DIRECT_PARAMS.max_voltage, i_list=[-x for x in I_list])
                logger.log(4, "V source")
                data.extend(
                    k2410.iv_wizard(i_compliance=-IV_REVERSE_PARAMS.current_compliance, v_list=[-x for x in V_list]))

                rows = [[d.timestamp, -d.current, -d.voltage] for d in data]
                diode_save(COLUMNS, rows, PATH, VI_NAMES, test_datas)

                delay = arduino.relay_mux(ArduinoCarac.Channels.SURGE)
                tme.sleep(delay + .5)
                delay = arduino.relay_mes(diode.board, True)
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
                        "loup.plantevin@insa-lyon.fr"],
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
                    "loup.plantevin@insa-lyon.fr"],
                   "Surge ended", f"Test terminated\nSuccess ?\n{DIODE_MAP}")
