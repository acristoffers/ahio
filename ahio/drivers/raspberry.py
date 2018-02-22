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

import ahio.abstract_driver

import os.path
import platform
import re
from enum import Enum


def pi_version():
    """Detect the version of the Raspberry Pi.  Returns either 1, 2 or
    None depending on if it's a Raspberry Pi 1 (model A, B, A+, B+),
    Raspberry Pi 2 (model B+), or not a Raspberry Pi.
    https://github.com/adafruit/Adafruit_Python_GPIO/blob/master/Adafruit_GPIO/Platform.py
    """
    if not os.path.isfile('/proc/cpuinfo'):
        return None
    # Check /proc/cpuinfo for the Hardware field value.
    # 2708 is pi 1
    # 2709 is pi 2
    # Anything else is not a pi.
    with open('/proc/cpuinfo', 'r') as infile:
        cpuinfo = infile.read()
    # Match a line like 'Hardware   : BCM2709'
    match = re.search('^Hardware\s+:\s+(\w+)$', cpuinfo,
                      flags=re.MULTILINE | re.IGNORECASE)
    if not match:
        # Couldn't find the hardware, assume it isn't a pi.
        return None
    if match.group(1) == 'BCM2708':
        # Pi 1
        return 1
    elif match.group(1) == 'BCM2709':
        # Pi 2
        return 2
    elif match.group(1) == 'BCM2835':
        # Pi 3
        return 3
    else:
        # Something else, not a pi.
        return None


class ahioDriverInfo(ahio.abstract_driver.AbstractahioDriverInfo):
    NAME = 'Raspberry'
    AVAILABLE = pi_version() is not None


# Just try to import it. Code that depends on it should not be executed outside
# of Raspberry Pi anyway
try:
    import RPi.GPIO as GPIO
except ImportError:
    if ahioDriverInfo.AVAILABLE:
        print("RPi.GPIO not installed: sudo apt-get install python3-rpi.gpio")
        ahioDriverInfo.AVAILABLE = false
except RuntimeError:
    ahioDriverInfo.AVAILABLE = false
    print("You probably need superuser privileges. Try running with sudo")


class Driver(ahio.abstract_driver.AbstractDriver):

    Pins = Enum(
        'Pins',
        'D3 D5 D7 D8 D10 D12 D13 D15 D16 D18 D19 D21 D22 D23 D24 D26')

    __pwm = {}
    __pwm_frequency = {}

    def __init__(self):
        if ahioDriverInfo.AVAILABLE:
            GPIO.setmode(GPIO.BOARD)
            for pin in Driver.Pins:
                self._set_pin_direction(pin, ahio.Direction.Output)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        GPIO.cleanup()

    def __create_pin_info(self, pid):
        return {
            'id': pid,
            'name': 'Digital %s' % self.__pin_to_int(pid),
            'analog': {
                'input': False,
                'output': False,
                'read_range': None,
                'write_range': None
            },
            'digital': {
                'input': True,
                'output': True,
                'pwm': True
            }
        }

    def __pin_to_int(self, pin):
        if type(pin) is int:
            return pin
        else:
            return int(pin.name.replace('D', ''))

    def __clamp(self, value, min, max):
        return sorted((min, value, max))[1]

    # pinout used is the second on this link (physical/BOARD pinout):
    # https://www.raspberrypi.org/documentation/usage/gpio
    def available_pins(self):
        return [self.__create_pin_info(pin) for pin in Driver.Pins]

    def _set_pin_direction(self, pin, direction):
        pin = self.__pin_to_int(pin)
        if direction == ahio.Direction.Input:
            GPIO.setup(pin, GPIO.IN)
        else:
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
        self.__pwm.pop(pin, None)

    def _pin_direction(self, pin):
        pin = self.__pin_to_int(pin)
        function = GPIO.gpio_function(pin)
        if function == GPIO.IN:
            return ahio.Direction.Input
        elif function == GPIO.OUT or function == GPIO.PWM:
            return ahio.Direction.Output
        else:
            return None

    def _set_pin_type(self, pin, ptype):
        if ptype != ahio.PortType.Digital:
            raise RuntimeError('Raspberry Pi pins can only be used as Digital')

    def _pin_type(self, pin):
        return ahio.PortType.Digital

    def _write(self, pin, value, pwm):
        pin = self.__pin_to_int(pin)
        if self._pin_direction(pin) == ahio.Direction.Input:
            return
        if pwm:
            if type(value) is int or type(value) is float:
                value = int(100 * self.__clamp(float(value), 0.0, 1.0))
                p = self.__pwm.get(pin, None)
                if not p:
                    freq = self.__pwm_frequency.get(pin, None)
                    if not freq:
                        freq = 1
                    p = GPIO.PWM(pin, freq)
                p.start(value)
            else:
                raise TypeError(
                    'Value should be a float or int between 0 and 1')
        else:
            if type(value) is ahio.LogicValue:
                lv = ahio.LogicValue
                value = GPIO.HIGH if value == lv.High else GPIO.LOW
                GPIO.output(pin, value)
            else:
                raise TypeError('Value should be of type ahio.LogicValue')

    def _read(self, pin):
        pin = self.__pin_to_int(pin)
        return GPIO.input(pin)

    def analog_references(self):
        return []

    def _set_analog_reference(self, reference, pin):
        raise RuntimeError('Raspberry Pi does not have analog pins')

    def _analog_reference(self, pin):
        raise RuntimeError('Raspberry Pi does not have analog pins')

    def _set_pwm_frequency(self, frequency, pin):
        if pin:
            pin = self.__pin_to_int(pin)
            self.__pwm_frequency[pin] = frequency
            pwm = self.__pwm.get(pin, None)
            if pwm:
                pwm.ChangeFrequency(frequency)
        else:
            for pin in Driver.Pins:
                self._set_pwm_frequency(frequency, pin)
