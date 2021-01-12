from enum import Enum
from typing import TypeVar, List, Tuple
import time as tme

import visa


class DG4062:
    # ################# #
    # ## F/AWG enums ## #
    # ################# #

    class Shapes(Enum):
        """An enumeration of all the possible shapes."""
        SINUSOID = "SIN"
        SQUARE = "SQU"
        RAMP = "RAMP"
        PULSE = "PULS"
        NOISE = "NOIS"
        USER = "USER"
        HARMONIC = "HARM"
        CUSTOM = "CUST"
        DC = "DC"
        ABSSINE = "ABSSINE"
        ABSSINEHALF = "ABSSINEHALF"
        AMPALT = "AMPALT"
        ATTALT = "ATTALT"
        GAUSSPULSE = "GAUSSPULSE"
        NEGRAMP = "NEGRAMP"
        NPULSE = "NPULSE"
        PPULSE = "PPULSE"
        SINETRA = "SINETRA"
        SINEVER = "SINEVER"
        STAIRDN = "STAIRDN"
        STAIRUD = "STAIRUD"
        STAIRUP = "STAIRUP"
        TRAPEZIA = "TRAPEZIA"
        BANDLIMITED = "BANDLIMITED"
        BUTTERWORTH = "BUTTERWORTH"
        CHEBYSHEV1 = "CHEBYSHEV1"
        CHEBYSHEV2 = "CHEBYSHEV2"
        COMBIN = "COMBIN"
        CPULSE = "CPULSE"
        CWPULSE = "CWPULSE"
        DAMPEDOSC = "DAMPEDOSC"
        DUALTONE = "DUALTONE"
        GAMMA = "GAMMA"
        GATEVIBR = "GATEVIBR"
        LFMPULSE = "LFMPULSE"
        MCNOSIE = "MCNOSIE"
        NIMHDISCHARGE = "NIMHDISCHARGE"
        PAHCUR = "PAHCUR"
        QUAKE = "QUAKE"
        RADAR = "RADAR"
        RIPPLE = "RIPPLE"
        ROUNDHALF = "ROUNDHALF"
        ROUNDPM = "ROUNDPM"
        STEPRESP = "STEPRESP"
        SWINGOSC = "SWINGOSC"
        TV = "TV"
        VOICE = "VOICE"
        THREEAM = "THREEAM"
        THREEFM = "THREEFM"
        THREEPM = "THREEPM"
        THREEPWM = "THREEPWM"
        THREEPFM = "THREEPFM"
        CARDIAC = "CARDIAC"
        EOG = "EOG"
        EEG = "EEG"
        EMG = "EMG"
        PULSILOGRAM = "PULSILOGRAM"
        RESSPEED = "RESSPEED"
        LFPULSE = "LFPULSE"
        TENS1 = "TENS1"
        TENS2 = "TENS2"
        TENS3 = "TENS3"
        IGNITION = "IGNITION"
        ISO167502SP = "ISO167502SP"
        ISO167502VR = "ISO167502VR"
        ISO76372TP1 = "ISO76372TP1"
        ISO76372TP2A = "ISO76372TP2A"
        ISO76372TP2B = "ISO76372TP2B"
        ISO76372TP3A = "ISO76372TP3A"
        ISO76372TP3B = "ISO76372TP3B"
        ISO76372TP4 = "ISO76372TP4"
        ISO76372TP5A = "ISO76372TP5A"
        ISO76372TP5B = "ISO76372TP5B"
        SCR = "SCR"
        SURGE = "SURGE"
        AIRY = "AIRY"
        BESSELJ = "BESSELJ"
        BESSELY = "BESSELY"
        CAUCHY = "CAUCHY"
        CUBIC = "CUBIC"
        DIRICHLET = "DIRICHLET"
        ERF = "ERF"
        ERFC = "ERFC"
        ERFCINV = "ERFCINV"
        ERFINV = "ERFINV"
        EXPFALL = "EXPFALL"
        EXPRISE = "EXPRISE"
        GAUSS = "GAUSS"
        HAVERSINE = "HAVERSINE"
        LAGUERRE = "LAGUERRE"
        LAPLACE = "LAPLACE"
        LEGEND = "LEGEND"
        LOG = "LOG"
        LOGNORMAL = "LOGNORMAL"
        LORENTZ = "LORENTZ"
        MAXWELL = "MAXWELL"
        RAYLEIGH = "RAYLEIGH"
        VERSIERA = "VERSIERA"
        WEIBULL = "WEIBULL"
        X2DATA = "X2DATA"
        COSH = "COSH"
        COSINT = "COSINT"
        COT = "COT"
        COTHCON = "COTHCON"
        COTHPRO = "COTHPRO"
        CSCCON = "CSCCON"
        CSCPRO = "CSCPRO"
        CSCHCON = "CSCHCON"
        CSCHPRO = "CSCHPRO"
        RECIPCON = "RECIPCON"
        RECIPPRO = "RECIPPRO"
        SECCON = "SECCON"
        SECPRO = "SECPRO"
        SECH = "SECH"
        SINC = "SINC"
        SINH = "SINH"
        SININT = "SININT"
        SQRT = "SQRT"
        TAN = "TAN"
        TANH = "TANH"
        ACOS = "ACOS"
        ACOSH = "ACOSH"
        ACOTCON = "ACOTCON"
        ACOTPRO = "ACOTPRO"
        ACOTHCON = "ACOTHCON"
        ACOTHPRO = "ACOTHPRO"
        ACSCCON = "ACSCCON"
        ACSCPRO = "ACSCPRO"
        ACSCHCON = "ACSCHCON"
        ACSCHPRO = "ACSCHPRO"
        ASECCON = "ASECCON"
        ASECPRO = "ASECPRO"
        ASECH = "ASECH"
        ASIN = "ASIN"
        ASINH = "ASINH"
        ATAN = "ATAN"
        ATANH = "ATANH"
        BARLETT = "BARLETT"
        BARTHANN = "BARTHANN"
        BLACKMAN = "BLACKMAN"
        BLACKMANH = "BLACKMANH"
        BOHMANWIN = "BOHMANWIN"
        BOXCAR = "BOXCAR"
        CHEBWIN = "CHEBWIN"
        FLATTOPWIN = "FLATTOPWIN"
        HAMMING = "HAMMING"
        HANNING = "HANNING"
        KAISER = "KAISER"
        NUTTALLWIN = "NUTTALLWIN"
        PARZENWIN = "PARZENWIN"
        TAYLORWIN = "TAYLORWIN"
        TRIANG = "TRIANG"
        TUKEYWIN = "TUKEYWIN"

    class Channels(Enum):
        """An enumeration for each output of the A/FWG"""
        OUT1 = "SOUR1"
        OUT2 = "SOUR2"

    class VoltUnits(Enum):
        """An enumeration for the used voltage units"""
        VPP = "VPP"
        VRMS = "VRMS"
        DBM = "DBM"

    class TrigSources(Enum):
        """An enumeration to selct the trigger mode"""
        INTERNAL = "INT"
        EXTERNAL = "EXT"
        MANUAL = "MAN"

    @staticmethod
    # TODO: def __parse_enum(enum: Enum[EnumMember], s: str) -> EnumMember:
    def __parse_enum(enum, s: str):
        """Transform a string to an enum member

        :param enum: the enum class.
        :param s: the enum member value's string.
        :return: the enum member.

        >>>DG4062.__parse_enum(DG4062.Status, 'RUN')
        <Status.RUN: 'RUN'>
        """
        for e in enum:
            if e.value in s:
                return e

        raise KeyError()

    # ############# #
    # ## Methods ## #
    # ############# #

    NAME = "DG4062"

    def __init__(self, instr):
        """Initialize the instrument.
        More than one instrument can be instanced.

        :param instr: the value returned by VisaController.get_instruments_by_name(...).
        :raise TypeError: "Instrument is not a DG4062 !" : specified instrument must be a DG4062.

        >>>from VISA.VISA_controller import VisaController
        ...from VISA.DG4062 import DG4062
        ...vc = VisaController()
        ...ds = DG4062(vc.get_instruments_by_name(DG4062.NAME)[0])

        """
        self.__device = instr.device

        if DG4062.NAME not in self.__device.query("*IDN?"):
            raise TypeError("Instrument is not a DG4062 !")

    def beep(self):
        """Produce a beep"""
        self.__device.write(f":SYST:BEEP:STAT 1")
        self.__device.write(f":SYST:BEEP")

    # ## Shape related methods ## #
    def set_chn_shape(self, chn: Channels, shape: Shapes):
        """Set the shape of the specified channel."""
        self.__device.write(f":{chn.value}:FUNC:SHAP {shape.value}")

    def get_chn_shape(self, chn: Channels) -> Shapes:
        """Get the shape of the specified channel."""
        return DG4062.__parse_enum(DG4062.Shapes, self.__device.query(f":{chn.value}:FUNC:SHAP?"))

    # ## Time related methods ## #
    def set_chn_frequency(self, chn: Channels, freq: float):
        """Set the frequency of the specified channel."""
        self.__device.write(f":{chn.value}:FREQ:FIX {freq}")

    def get_chn_frequency(self, chn: Channels) -> float:
        """Get the frequency of the specified channel."""
        return float(self.__device.query(f":{chn.value}:FREQ:FIX?"))

    def set_chn_period(self, chn: Channels, period: float):
        """Set the period of the specified channel."""
        self.__device.write(f":{chn.value}:PER:FIX {period}")

    def get_chn_period(self, chn: Channels) -> float:
        """Get the period of the specified channel."""
        return float(self.__device.query(f":{chn.value}:PER:FIX?"))

    # ## Voltage related methods ## #
    def set_chn_volt_unit(self, chn: Channels, unit: VoltUnits):
        """Set the voltage unit for the specified channel."""
        self.__device.write(f":{chn.value}:VOLT:UNIT {unit.value}")

    def get_chn_volt_unit(self, chn: Channels) -> VoltUnits:
        """Get the voltage unit for the specified channel."""
        return DG4062.__parse_enum(DG4062.VoltUnits, self.__device.query(f":{chn.value}:VOLT:UNIT?"))

    def set_chn_hi_lo(self, chn: Channels, high: float, low: float):
        """Set the High and Low levels of the specified channel."""
        self.__device.write(f":{chn.value}:VOLT:HIGH {high}")
        self.__device.write(f":{chn.value}:VOLT:LOW {low}")

    def get_chn_hi_lo(self, chn: Channels) -> Tuple[float, float]:
        """Get the High and Low levels of the specified channel."""
        high = float(self.__device.query(f":{chn.value}:VOLT:HIGH?"))
        low = float(self.__device.query(f":{chn.value}:VOLT:LOW?"))
        return high, low

    def set_chn_amp_off(self, chn: Channels, amplitude: float, offset: float):
        """Set the Amplitude and Offset levels of the specified channel."""
        self.__device.write(f":{chn.value}:VOLT:AMPL {amplitude}")
        self.__device.write(f":{chn.value}:VOLT:OFFS {offset}")

    def get_chn_amp_off(self, chn: Channels) -> Tuple[float, float]:
        """Get the Amplitude and Offset levels of the specified channel."""
        amplitude = float(self.__device.query(f":{chn.value}:VOLT:AMPL?"))
        offset = float(self.__device.query(f":{chn.value}:VOLT:OFFS?"))
        return amplitude, offset

    # ## Pulse related methods ## #
    def set_chn_pulse_duty(self, chn: Channels, duty: float):
        """Set the duty cycle of the specified channel."""
        self.__device.write(f":{chn.value}:PULS:DCYC {duty}")

    def get_chn_pulse_duty(self, chn: Channels) -> float:
        """Get the duty cycle of the specified channel."""
        return float(self.__device.query(f":{chn.value}:PULS:DCYC?"))

    def set_chn_pulse_width(self, chn: Channels, width: float):
        """Set the width of the specified channel."""
        self.__device.write(f":{chn.value}:PULS:WIDT {width}")

    def get_chn_pulse_width(self, chn: Channels) -> float:
        """Get the width of the specified channel."""
        return float(self.__device.query(f":{chn.value}:PULS:WIDT?"))

    # ## Burst related methods ## #
    def chn_burst(self, chn: Channels, on: bool):
        """Enable/Disable Burst mode."""
        self.__device.write(f":{chn.value}:BURS:STATE {'ON' if on else 'OFF'}")

    def is_chn_burst(self, chn: Channels) -> bool:
        """Check Burst mode is enabled."""
        return self.__device.query(f":{chn.value}:BURS:STATE?") == "ON"

    def set_chn_burst_trig(self, chn: Channels, source: TrigSources):
        """Set the source of the burst trigger for the specified channel."""
        self.__device.write(f":{chn.value}:BURS:TRIG:SOUR {source.value}")

    def get_chn_burst_trig(self, chn: Channels) -> TrigSources:
        """Get the source of the burst trigger for the specified channel."""
        return DG4062.__parse_enum(DG4062.TrigSources, self.__device.query(f":{chn.value}:BURS:TRIG:SOUR?"))

    def chn_burst_trig(self, chn: Channels):
        """Trigger a burst (manually)."""
        self.set_chn_burst_trig(chn, DG4062.TrigSources.MANUAL)
        self.__device.write(f":{chn.value}:BURS:TRIG")

    # ################ #
    # ## Attributes ## #
    # ################ #

    # ## Global attributes ## #
    @property
    def out1(self) -> bool:
        """Check/Enable the output 1"""
        return self.__device.query(":OUTP1:STATE?") == "ON"

    @out1.setter
    def out1(self, out: bool):
        """Enable/Disable output 1"""
        self.__device.write(f":OUTP1:STATE {'ON' if out else 'OFF'}")

    @property
    def out2(self) -> bool:
        """Check/Enable the output 2"""
        return self.__device.query(":OUTP2:STATE?") == "ON"

    @out2.setter
    def out2(self, out: bool):
        """Enable/Disable output 2"""
        self.__device.write(f":OUTP2:STATE {'ON' if out else 'OFF'}")

    # ############ #
    # ## ERRORS ## #
    # ############ #
    @property
    def errors(self):
        """Get a list of the fawg errors."""
        return self.__device.query(':SYST:ERR?')


if __name__ == "__main__":
    from VISA_controller import VisaController
    import time

    vc = VisaController(query='TCPIP[0-9]*::192.168.0.[0-9]*::inst[0-9]*::INSTR', verbose=True)
    inst = vc.get_instruments_by_name(DG4062.NAME)[0]
    dg = DG4062(inst)

    CHN1 = DG4062.Channels.OUT1
    pulses = [x / 2 for x in range(1, 8)]

    dg.set_chn_shape(CHN1, DG4062.Shapes.PULSE)
    dg.set_chn_period(CHN1, 500e-6)
    dg.set_chn_pulse_width(CHN1, 300e-6)
    dg.chn_burst(CHN1, True)
    dg.out1 = True
    dg.beep()

    print(dg.errors)

    for p in pulses:
        dg.set_chn_hi_lo(CHN1, p, -.1)
        dg.chn_burst_trig(CHN1)
        dg.beep()
        time.sleep(1)

    print(dg.errors)

