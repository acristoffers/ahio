# -*- coding: utf-8; -*-
#
# Copyright (c) 2016 Álan Crístoffer
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""@package ahio
ahio provides access to various I/O devices.

This package provides abstracted access to various digital and analogic I/O
devices, such as Arduino, Raspberry PI, MyRIO and PLC. It allows the developer
to write and read data from such devices without needing to worry about the
specifics of each device, and to easily switch devices without code
refactoring.

The functions in this package list and instantiate the drivers. For the driver
api, see `ahio.abstract_driver.AbstractDriver`. Driver metadata format can be
found in `ahio.abstract_driver.AbstractahioDriverInfo`

@author Álan Crístoffer <acristoffers@gmail.com>
"""

from enum import Enum

import ahio.drivers

__author__ = 'Álan Crístoffer'
__copyright__ = 'Copyright 2016, Álan Crístoffer'
__credits__ = ['Álan Crístoffer']
__license__ = 'MIT'
__version__ = '1.0.19'
__maintainer__ = 'Álan Crístoffer'
__email__ = 'acristoffers@gmail.com'
__status__ = 'Release'

PortType = Enum('PortType', 'Analog Digital')
Direction = Enum('Direction', 'Output Input')
LogicValue = Enum('LogicValue', 'Low High')


def add_path(path):
    """Adds a directory to the list of folders where to load drivers from"""
    drivers.add_path(path)


def remove_path(path):
    """Removes a directory from the list of folders where to load drivers from"""
    drivers.remove_path(path)


def clear_path():
    """Clears the list of folders where to load drivers from"""
    drivers.clear_path()


def list_available_drivers():
    """Returns a list of string with the names of available drivers.

    Available means that the driver is installed and can be used. For example,
    it will not contain "Raspberry" if you're not running on a Raspberry Pi,
    even if the raspberry.py script is present in the drivers directory.

    @returns a list of strings that can be fed to `ahio.new_driver` to get an
    instance of the desired driver.
    """
    return drivers.available_drivers()


def driver_info(name):
    """Returns driver metadata.

    Returns a class which static properties contains metadata from the
    driver, such as name and availability.

    @returns a subclass from `ahio.abstract_driver.AbstractahioDriverInfo` with
    metadata from the driver.
    """
    return drivers.driver_info(name)


def new_driver(name):
    """Instantiates a new object of the named driver.

    The API used by the returned object can be seen in
    `ahio.abstract_driver.AbstractDriver`

    @returns a Driver object from the required type or None if it's not
    available
    """
    return drivers.new_driver_object(name)
