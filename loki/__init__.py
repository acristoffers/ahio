"""@package loki
Loki provides access to various I/O devices.

This package provides abstracted access to various digital and analogic I/O
devices, such as Arduino, Raspberry PI, MyRIO and PLC. It allows the developer
to write and read data from such devices without needing to worry about the
specifics of each device, and to easily switch devices without code
refactoring.

The functions in this package list and instantiate the drivers. For the driver
api, see `loki.abstract_driver.AbstractDriver`. Driver metadata format can be
found in `loki.abstract_driver.AbstractLokiDriverInfo`

@author Álan Crístoffer <acristoffers@gmail.com>
"""

from enum import Enum
import loki.drivers

__version__ = '1.0.0'

PortType = Enum('PortType', 'Analog Digital')
Direction = Enum('Direction', 'Output Input')
LogicValue = Enum('LogicValue', 'Low High')


def list_available_drivers():
    """Returns a list of string with the names of available drivers.

    Available means that the driver is installed and can be used. For example,
    it will not contain "Raspberry" if you're not running on a Raspberry Pi,
    even if the raspberry.py script is present in the drivers directory.

    @returns a list of strings that can be fed to `loki.new_driver` to get an
    instance of the desired driver.
    """
    return drivers.available_drivers()


def driver_info(name):
    """Returns driver metadata.

    Returns a class which static properties contains metadata from the
    driver, such as name and availability.

    @returns a subclass from `loki.abstract_driver.AbstractLokiDriverInfo` with
    metadata from the driver.
    """
    return drivers.driver_info(name)


def new_driver(name):
    """Instantiates a new object of the named driver.

    The API used by the returned object can be seen in
    `loki.abstract_driver.AbstractDriver`

    @returns a Driver object from the required type of None if it's not
    available
    """
    return drivers.new_driver_object(name)
