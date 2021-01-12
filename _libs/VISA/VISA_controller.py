import time
from collections import namedtuple
from typing import List, Tuple

import visa
import pyvisa


class VisaController:
    Instrument = namedtuple('Instrument', ['idn', 'device'])
    Instrument.__doc__ = """Store an instrument."""
    Instrument.idn.__doc__ += """ : Identity of the instrument. See Identity."""
    Instrument.device.__doc__ += """ : Physical device."""

    Identity = namedtuple('Identity', ['mnf', 'name', 'sn', 'ver'])
    Identity.__doc__ = """Identity of an Instrument."""
    Identity.mnf.__doc__ += """ : Name of the manufacturer."""
    Identity.name.__doc__ += """ : Name of the device."""
    Identity.sn.__doc__ += """ : Serial number."""
    Identity.ver.__doc__ += """ : Version."""

    __instr_list = {}
    __rm = None
    __query = None

    @classmethod
    def __init__(cls, *, query: str = '?*::INSTR', verbose: bool = False):
        """Initialisation of the visa controller.
        There should be only one instance of the controller.
        This will initiate a connected device listing.

        Typical query :
         * 'TCPIP[0-9]*::[0-9]*.[0-9]*.[0-9]*.[0-9]*::inst[0-9]*::INSTR' #All IPs
         * 'TCPIP[0-9]*::192.168.0.[0-9]*::inst[0-9]*::INSTR'  # Only local

        :param query: string to refine the querry
        :param verbose: blah ?
        """

        cls.__query = query
        cls.__rm = visa.ResourceManager()

        cls.__instr_list = {}
        cls.list_devices(verbose=verbose)

    @classmethod
    def __del__(cls):
        for res in cls.__instr_list:
            try:
                cls.__instr_list[res].device.close()
            except (visa.VisaIOError, visa.InvalidSession):
                pass

            # TODO: del cls.__instr_list[res]

    @classmethod
    def test_devices(cls, *, verbose: bool = False):
        """Test the current list of instruments (and delete the unused).

        :param verbose: blah ?
        """
        temp = {}

        for res in cls.__instr_list:
            # Ping the instrument
            try:
                idn = cls.__instr_list[res].device.query('*IDN?')
            except (visa.VisaIOError, visa.InvalidSession) as e:
                if verbose:
                    print(f"{res} seems disconnected ({e})\n")
            else:
                temp[res] = cls.__instr_list[res]
                if verbose:
                    print(f"{res} is connected (as {idn})\n")

        cls.__instr_list = temp

    @classmethod
    def list_devices(cls, *, query: str = None, verbose: bool = False):
        """Refresh and Retrieve all connected devices.

        :param query: string to refine the querry
        :param verbose: blah ?
        """
        # Set query
        query = query if query is not None else cls.__query

        # Refresh instruments list
        cls.test_devices()

        # Get all resources
        res_list = cls.__rm.list_resources(query=query)
        if verbose:
            print(f"\nResource list:\n{res_list}\n\n")

        for res in res_list:
            # Check if resource is not already used
            if res not in cls.__instr_list.keys():
                try:
                    # Open the resource
                    instr = cls.__rm.open_resource(res)
                    # Wait for serial port to begin (needed for arduino)
                    if 'ASRL' in res:
                        time.sleep(2)

                    # Retrieve the identifier and parse it
                    info = [x.strip() for x in instr.query('*IDN?').split(',')]
                    idn = VisaController.Identity(*info)
                except (visa.VisaIOError, visa.InvalidSession) as e:
                    if verbose:
                        print(f"{res} seems not connected, but listed ({e})\n")
                else:
                    # Create a new entry
                    cls.__instr_list[res] = VisaController.Instrument(idn, instr)
        if verbose:
            print(f"connected list : {cls.__instr_list}\n")

    @classmethod
    def get_instruments_by_name(cls, name: str) -> List[Instrument]:
        """Create a list of all connected instruments that have the specified name.

        :param name: the name string. Usually given by the device class.
        :return: a list of instrument
        """
        return [d for _, d in cls.__instr_list.items() if d.idn.name == name]

    @classmethod
    def get_unchecked_resource(cls, res: str) -> pyvisa.resources.Resource:
        """Try to open the resource, without any checking or warranty, use at your own risk !

        :param res: the resource id, like 'ASRL1::INSTR'
        :return: the requested resource
        """
        return cls.__rm.open_resource(res)

    @classmethod
    def get_resources_list(cls) -> Tuple[str]:
        """Get all the resource ids, to be used with get_unchecked_resource

        :return: all the resource ids
        """
        return cls.__rm.list_resources()


if __name__ == "__main__":
    vc = VisaController(verbose=True)
