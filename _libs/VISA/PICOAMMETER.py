from collections import namedtuple
from enum import Enum
from typing import List


class PICOAMMETER:
    Data = namedtuple('Data', ['current', 'timestamp', 'status'])
    Data.__doc__ = """Store a point of data returned by the picoammeter"""
    Data.current.__doc__ += """ : Value in Amps (float)"""
    Data.timestamp.__doc__ += """ : Time since start, in ms (float)"""
    Data.status.__doc__ += """ : Details about the reading (PICOAMMETER.Status)"""

    # ################ #
    # ## PICO enums ## #
    # ################ #

    class Speed(Enum):
        """An enumeration for the reading speed period."""
        SLOW = '5'
        MEDIUM = '1'
        FAST = '0.1'

    class Keys(Enum):
        """An enumeration that describe all the keys of the instrument."""
        CONFIG_LOCAL = "1"
        MENU = "17"
        MEDIAN = "2"
        AVERAGE = "3"
        MX_B = "4"
        M_X_B = "5"
        LOG = "6"
        REL = "7"
        ZERO_CHECK = "8"
        ZERO_COR = "16"
        COMM = "18"
        DISP = "19"
        TRIG = "20"
        HALT = "21"
        DIGITS = "22"
        RATE = "23"
        LEFT = "24"
        RIGHT = "15"
        SAVE = "26"
        SETUP = "27"
        STORE = "28"
        RECALL = "29"
        LIMIT = "30"
        AUTO_ZERO = "31"
        EXIT = "32"
        ENTER = "14"
        RANGE_UP = "11"
        AUTO = "12"
        RANGE_DOWN = "13"

    class Status(Enum):
        """An enumeration that describe the current status (errors) of the instrument."""
        OVERFLOW = (0, "Over-range during measurement")
        FILTER = (1, "Averaging filter is enabled")
        MATHS = (2, "CALC1 is enabled")
        NULL = (3, "Null on CALC2 is enabled")
        LIMITS = (4, "Limit test on CALC2 is enabled")
        LIM1 = (5, "CALC2:LIM1 test failed")
        LIM2 = (6, "CALC2:LIM2 test failed")
        OVERVOLTAGE = (7, "Overvoltage during measurement")
        ZERO_CHECK = (9, "Zero check is enabled")
        ZERO_CORRECT = (10, "Zero correct is enabled")

    @staticmethod
    # TODO: def __parse_enum(enum: Enum[EnumMember], s: str) -> EnumMember:
    def __parse_enum(enum, s: str):
        """Transform a string to an enum member

        :param enum: the enum class.
        :param s: the enum member value's string.
        :return: the enum member.

        >>>PICOAMMETER.__parse_enum(PICOAMMETER.Speed, '5')
        <Speed.SLOW: '5'>
        """
        for e in enum:
            if e.value in s:
                return e

        raise KeyError()

    @staticmethod
    def __list_errors(enum, val: int) -> List:
        """Return a list of error enum member, corresponding to the value of val.

        :param enum: the error enum class.
        :param val: the error value from the instrument.
        :return: a list of error enum member.
        """
        return [e for e in enum if ((val >> e.value[0]) & 1) == 1]

    # ############# #
    # ## Methods ## #
    # ############# #

    NAME = "MODEL 6485"

    def __init__(self, instr):
        """Initialize the instrument.
        More than one instrument can be instanced.

        :param instr: the value returned by VisaController.get_instruments_by_name(...).
        :raise TypeError: "Instrument is not a Keithley 6485 !" : specified instrument must be a Keithley 6485.

        >>>from VISA.VISA_controller import VisaController
        ...from VISA.PICOAMMETER import PICOAMMETER
        ...vc = VisaController()
        ...pico = PICOAMMETER(vc.get_instruments_by_name(PICOAMMETER.NAME)[0])

        """
        self.__device = instr.device

        if PICOAMMETER.NAME not in self.__device.query("*IDN?"):
            raise TypeError("Instrument is not a Keithley 6485 !")

    def read(self) -> List[Data]:
        """Read a new value from the picoammeter.

        :return: a list of Data('current', 'timestamp', 'status')
        """
        readings = self.__device.query(":READ?").split(',')  # Split by ','
        readings = [float(x.replace('A', '')) for x in readings]  # Convert to float
        readings[2::3] = [PICOAMMETER.__list_errors(PICOAMMETER.Status, int(x))
                          for x in readings[2::3]]  # Evaluate status bits
        readings = [readings[i:i + 3] for i in range(0, len(readings), 3)]  # Split every 3 items
        data = [PICOAMMETER.Data(*x) for x in readings]  # Create data list
        return data

    # ################ #
    # ## Attributes ## #
    # ################ #

    # ## Global attributes ## #
    @property
    def text1(self) -> str:
        """Get/Set the custom display text, line 1 (max width of 12 char)."""
        return self.__device.query(":DISP:WIND1:TEXT:DATA?")

    @text1.setter
    def text1(self, txt: str):
        txt = txt[:12] if len(txt) > 12 else txt
        self.__device.write(f':DISP:WIND1:TEXT:DATA "{txt}"')

    @property
    def text1_dis(self) -> bool:
        """Check if displayed/Display the custom display text, line 1."""
        return self.__device.query(":DISP:WIND1:TEXT:STAT?") == "1"

    @text1_dis.setter
    def text1_dis(self, display: bool):
        self.__device.write(f":DISP:WIND1:TEXT:STAT {'1' if display else '0'}")

    # ## Measure attributes ## #

    # ## Measure setup attributes ## #
    @property
    def range(self) -> float:
        """Get/Set the range of measure (Amps)"""
        return float(self.__device.query(":RANG?"))

    @range.setter
    def range(self, rng: float):
        self.__device.write(f":RANG {rng}")

    @property
    def speed(self) -> Speed:
        """Get/Set the measurement speed (analog mean)."""
        return PICOAMMETER.__parse_enum(PICOAMMETER.Speed, self.__device.query(":SENS:CURR:NPLC?"))

    @speed.setter
    def speed(self, spd: Speed):
        self.__device.write(f":SENS:CURR:NPLC {spd.value}")

    @property
    def auto_zero(self) -> bool:
        """Check/Set Auto-zero before each measurement."""
        return self.__device.query(":SYST:AZER?") == "1"

    @auto_zero.setter
    def auto_zero(self, azer: bool):
        self.__device.write(f":SYST:AZER {'1' if azer else '0'}")

    @property
    def zero_check(self) -> bool:
        """Check/Set Zero-check (disconnect input and force to short)."""
        return self.__device.query(":SYST:ZCH?") == "1"

    @zero_check.setter
    def zero_check(self, zch: bool):
        self.__device.write(f":SYST:ZCH {'1' if zch else '0'}")

    @property
    def zero_correction(self) -> bool:
        """Check/Set Zero correction of the measure (relative measurement)."""
        return self.__device.query(":SYST:ZCOR?") == "1"

    @zero_correction.setter
    def zero_correction(self, zcor: bool):
        self.__device.write(f":SYST:ZCOR {'1' if zcor else '0'}")

    @property
    def trig_count(self) -> int:
        """Get/Set the number of measurement to take in each burst (between 0 and 2500)."""
        return int(self.__device.query(":TRIG:COUN?"))

    @trig_count.setter
    def trig_count(self, count: int):
        if not 0 <= count <= 2500:
            raise ValueError("Count must be between 0 and 2500")
        self.__device.write(f":TRIG:COUN {count}")

    @property
    def arm_count(self) -> int:
        """Get/Set the number of burst of measurement to make (between 0 and 2500)."""
        return int(self.__device.query(":ARM:COUN?"))

    @arm_count.setter
    def arm_count(self, count: int):
        if not 0 <= count <= 2500:
            raise ValueError("Count must be between 0 and 2500")
        self.__device.write(f":ARM:COUN {count}")

    # ## Measure treatments attributes ## #
    @property
    def median(self) -> int:
        """Get/Set the Median filter rank (between 0 and 5)."""
        if self.__device.query(":SENS:MED:STAT?") == "0":
            return 0
        else:
            return int(self.__device.query(":SENS:MED:RANK?"))

    @median.setter
    def median(self, rank: int):
        if not 0 <= rank <= 5:
            raise ValueError("Rank must be between 0 and 5")
        if rank == 0:
            self.__device.write(":SENS:MED:STAT 0")
        else:
            self.__device.write(":SENS:MED:RANK {rank}")
            self.__device.write(":SENS:MED:STAT 1")

    @property
    def average(self) -> int:
        """Get/Set the Average filter count (between 0 and 100)."""
        if self.__device.query(":SENS:AVER:STAT?") == "0":
            return 0
        else:
            return int(self.__device.query(":SENS:AVER:COUN?"))

    @average.setter
    def average(self, count: int):
        if not 0 <= count <= 100:
            raise ValueError("Count must be between 0 and 100")
        if count == 0:
            self.__device.write(":SENS:AVER:STAT 0")
        else:
            self.__device.write(":SENS:AVER:COUN {count}")
            self.__device.write(":SENS:AVER:STAT 1")


if __name__ == "__main__":
    from VISA_controller import VisaController
    import time

    vc = VisaController(query='?*::INSTR', verbose=True)
    inst = vc.get_instruments_by_name(PICOAMMETER.NAME)[0]
    pico = PICOAMMETER(inst)

    pico.arm_count = 1
    pico.trig_count = 5
    print(pico.read())
