from collections import namedtuple
from enum import Enum

import Arduino.BuildArduino as BuildArduino
from VISA.VISA_controller import VisaController


class ArduinoCarac:
    NAME = "Carac_test"
    VERSION = "V1.31"

    __ARDUINO_PATH = '.\\Carac\\'
    __arduino_args = [  # '-v',
        '-W', 'C:\\Program Files\\Arduino\\hardware\\arduino\\avr\\cores\\arduino',
        '-V', 'C:\\Program Files\\Arduino\\hardware\\arduino\\avr\\variants',
        '--dude-conf=C:\\Program Files\\Arduino\\hardware\\tools\\avr\\etc\\avrdude.conf',
        '-l', 'C:\\Program Files\\Arduino\\hardware\\arduino\\avr\\libraries\\Wire\\src',
        '-l', 'C:\\Program Files\\Arduino\\hardware\\arduino\\avr\\libraries\\Wire\\src\\utility',
        '-l', '.\\Carac\\MCP342x\\src',
        '--arch', 'atmega2560',
        '--core', 'wiring',
        '-b', 'mega',
        '-u', '',
        '-d', __ARDUINO_PATH
    ]
    
    Data = namedtuple('Data', ['raw', 'voltage', 'error'])
    Data.__doc__ = """Store a point of data returned by the ADC"""
    Data.raw.__doc__ += """ : Raw value from the ADC (16bits signed) (int)"""
    Data.voltage.__doc__ += """ : Converted voltage (float)"""
    Data.error.__doc__ += """ : True if the reading is errornous (bool)"""

    class Boards(Enum):
        A0 = "A0"
        A1 = "A1"
        A2 = "A2"
        A3 = "A3"
        A4 = "A4"
        A5 = "A5"
        A6 = "A6"
        B0 = "B0"
        B1 = "B1"
        B2 = "B2"
        B3 = "B3"
        B4 = "B4"
        B5 = "B5"
        B6 = "B6"

    class Channels(Enum):
        NONE = "0"
        MES = "1"
        HT = "2"
        SURGE = "3"

    class Gains(Enum):
        G1 = "1"
        G2 = "2"
        G4 = "4"
        G8 = "8"

    def __init__(self, instr: VisaController.Instrument):
        self.__device = instr.device

        if instr.idn.name != ArduinoCarac.NAME:
            raise TypeError("Instrument is not an Arduino !")

        # # Upload
        if instr.idn.ver != ArduinoCarac.VERSION:
            print(f"{instr.idn.ver} != {ArduinoCarac.VERSION} !\n Uploading new version...")

            ArduinoCarac.__arduino_args[-3] = self.__device.resource_info[0].alias
            self.__device.close()

            BuildArduino.main(ArduinoCarac.__arduino_args)

            self.__device.open()

    def surge(self, board: Boards) -> float:
        """Launch the surge sequence on the specified board

        :param board: select the board

        :return: estimated sequence duration in seconds
        """
        return int(self.__device.query(f":SURG {board.value}")) / 1000

    def htrb(self, board: Boards, on: bool) -> float:
        """Launch the HTRB sequence on the specified board

        :param board: select the board
        :param on: activate (True)/deactivate (False)

        :return: estimated sequence duration in seconds
        """
        return int(self.__device.query(f":HTRB {board.value},{'1' if on else '0'}")) / 1000

    def measure(self, board: Boards) -> float:
        """Launch the measure sequence on the specified board

        :param board: select the board

        :return: estimated sequence duration in seconds
        """
        return int(self.__device.query(f":MES {board.value}")) / 1000

    def read(self, board: Boards) -> Data:
        """Read the voltage across the current sensing resistor

        :param board: select the board

        :return: Data('raw', 'voltage', 'error')
        """
        ans = self.__device.query(f":READ {board.value}").split(',')  # Split by ','
        ans = [float(x.replace('V', '')) for x in ans]  # Convert to float
        data = ArduinoCarac.Data(*ans, ans == [-1, -1])

        return data

    def gain(self, gain: Gains) -> int:
        """Set the ADC gain

        :param gain: new gain of the ADCs

        :return: new gain
        """
        ans = self.__device.query(f":GAIN {gain.value}")
        try:
            ans = int(ans)
        except ValueError:
            pass

        return ans

    def stop(self):
        """Deactivate ALL relays.
        """
        return int(self.__device.query(f":STOP")) / 1000

    def relay_surge(self, board: Boards, on: bool):
        """Activate/deactivate the "surge" relay on the specified board
        This method is for debug only and shall not be used in production. Please use 'surge' instead.

        :param board: select the board
        :param on: activate (True)/deactivate (False)
        """
        return int(self.__device.query(f":RELA:SURG {board.value},{'1' if on else '0'}")) / 1000

    def relay_htrb(self, board: Boards, on: bool):
        """Activate/deactivate the "htrb" relay on the specified board
        This method is for debug only and shall not be used in production. Please use 'htrb' instead.

        :param board: select the board
        :param on: activate (True)/deactivate (False)
        """
        return int(self.__device.query(f":RELA:HT {board.value},{'1' if on else '0'}")) / 1000

    def relay_mes(self, board: Boards, on: bool):
        """Activate/deactivate the "mes" relay on the specified board
        This method is for debug only and shall not be used in production. Please use 'measure' instead.

        :param board: select the board
        :param on: activate (True)/deactivate (False)
        """
        return int(self.__device.query(f":RELA:MES {board.value},{'1' if on else '0'}")) / 1000

    def relay_mux(self, channel: Channels):
        """Select the main multiplexer position
        This method is for debug only and shall not be used in production.
        Please use 'surge', 'htrb' or 'measure' instead.

        :param channel: which channel to use
        """
        return int(self.__device.query(f":RELA:MUX {channel.value}")) / 1000

    def stop_relays(self, surge: bool, ht: bool, mes: bool):
        """Deactivate all the relays of a specified kind
        This method is not recommended for production.

        :param surge: deactivate (True)/do nothing (False)
        :param ht: deactivate (True)/do nothing (False)
        :param mes: deactivate (True)/do nothing (False)
        """
        code = 4 * surge + 2 * ht + 1 * mes
        return int(self.__device.query(f":BRDS:STOP {code}")) / 1000

    def orange(self, on: bool):
        """Activate/deactivate the orange light

        :param on: activate (True)/deactivate (False)
        """
        self.__device.write(f":LIGH:ORAN {'1' if on else '0'}")

    def red(self, on: bool):
        """Activate/deactivate the red light

        :param on: activate (True)/deactivate (False)
        """
        self.__device.write(f":LIGH:RED {'1' if on else '0'}")


if __name__ == "__main__":
    import pathlib, sys

    sys.path.append(str(pathlib.Path('../_libs/').resolve()))

    from VISA.VISA_controller import VisaController
    import time

    vc = VisaController(query='ASRL14::INSTR', verbose=True)
    inst = vc.get_instruments_by_name(ArduinoCarac.NAME)[0]
    arduino = ArduinoCarac(inst)
    Boards = arduino.Boards

    delay = arduino.surge(Boards.B2)
    time.sleep(delay + .5)
    arduino.red(True)
    time.sleep(2)
    arduino.relay_mux(arduino.Channels.HT)
