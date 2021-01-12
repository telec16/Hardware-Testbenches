import serial
import serial.tools.list_ports
from threading import Thread
from collections import namedtuple
import time


class Arduino(Thread):
    _INTERRUPT = '!'
    _GET = '?'
    _GET_ALL = '?'
    _CMD = '.'
    _SET = ':'
    _SEPARATOR = '|'
    _TERMINATOR = '\n'

    Data = namedtuple("Data", ["name", "value"])

    # # # # #
    # INIT  #
    # # # # #
    def __init__(self, callback, port=None, bauds=None, start_now=True):

        Thread.daemon = True
        super().__init__()

        # Instance var
        self.listening = False
        self.quit = False
        self.is_stop = False

        self.ser = None

        self.version = None
        self.readStack = []

        self.port = None
        self.bauds = None
        self.callback = None

        # Set callback
        self.callback = callback

        # Start thread
        self.start()

        # if port and bauds are gave, start listening
        if port is None or bauds is None:
            return

        self.bauds = bauds
        self.port = port

        if start_now:
            self.resume()

    # # THREAD # #

    # Soft buffer so it can peek and check whether its a interrupt data (!) or just a response
    def run(self):
        while not self.quit:
            if self.listening:
                line = self.ser.readline().decode("ASCII")
                if line.startswith(Arduino._INTERRUPT):
                    self.callback(line)
                else:
                    self.readStack.append(line)
        self.is_stop = True

    # Will stop the thread
    def stop(self):
        self.quit = True
        while not self.is_stop:
            pass
        if self.ser is not None and self.ser.is_open:
            self.ser.close()
        self.ser.__del__()

    # # STATIC METHODS # #

    @staticmethod
    def get_available_ports():
        return [comport.device for comport in serial.tools.list_ports.comports()]

    # # PUBLIC METHODS # #

    def get_version(self):
        return self.version

    def new_serial(self, port, bauds, start_now=True):
        self.pause()

        self.bauds = bauds
        self.port = port

        if start_now:
            self.resume()

    # Will pause and resume the serial communication, but not the thread
    def resume(self):
        self.ser = serial.Serial(self.port, self.bauds)
        self.version = self.ser.readline().decode("ASCII")
        self.readStack = []
        self.listening = True

    def pause(self):
        self.listening = False
        if self.ser is not None and self.ser.is_open:
            self.ser.close()

    # # PRIVATE METHODS # #

    # Soft buffer data read
    def _readline(self, timeout=-1):
        start_time = time.time()

        while len(self.readStack) == 0:
            if (timeout > 0) and ((start_time + timeout) <= time.time()):
                return ""

        return self.readStack.pop(0)

    @staticmethod
    def _parse_data(data):
        data_dict = {}

        lines = data.split(Arduino._SEPARATOR)

        for l in lines:
            d = l.split(Arduino._SET)
            data_dict[d[0]] = d[1]

        return data_dict

    @staticmethod
    def _filter_name(name):
        return ''.join(c for c in name if c.isalpha())

    def get_value(self, name):
        if self.ser is not None and self.ser.is_open:
            output = Arduino._filter_name(name) + Arduino._GET + Arduino._TERMINATOR
            self.ser.write(output.encode("ASCII"))
            return self._parse_data(self._readline())
        return False

    def get_values(self):
        if self.ser is not None and self.ser.is_open:
            self.ser.write((Arduino._GET_ALL + Arduino._TERMINATOR).encode("ASCII"))
            return self._parse_data(self._readline())
        return False

    def set_value(self, data):
        if self.ser is not None and self.ser.is_open:
            name, value = data
            output = Arduino._filter_name(name) + Arduino._SET + value + Arduino._TERMINATOR
            self.ser.write(output.encode("ASCII"))
            return True
        return False

    def set_cmd(self, cmd):
        if self.ser is not None and self.ser.is_open:
            output = Arduino._filter_name(cmd) + Arduino._CMD + Arduino._TERMINATOR
            self.ser.write(output.encode("ASCII"))
            return True
        return False
