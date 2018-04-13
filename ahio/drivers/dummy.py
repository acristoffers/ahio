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

from enum import Enum


class ahioDriverInfo(ahio.abstract_driver.AbstractahioDriverInfo):
    NAME = 'Dummy'
    AVAILABLE = True


class Driver(ahio.abstract_driver.AbstractDriver):
    Pins = Enum('Pins', 'Input Output')
    AnalogReferences = Enum('AnalogReferences', 'AR1 AR2')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def __create_pin_info(self, pid, pwm=False):
        return {
            'id': pid,
            'name': 'Pin %s' % pid.value,
            'analog': {
                'input': True,
                'output': True,
                'read_range': (0, 100),
                'write_range': (0, 100)
            },
            'digital': {
                'input': True,
                'output': True,
                'pwm': True
            }
        }

    def available_pins(self):
        return [self.__create_pin_info(pin) for pin in Driver.Pins]

    def _set_pin_direction(self, pin, direction):
        pass

    def _pin_direction(self, pin):
        return ahio.Direction.Input

    def _set_pin_type(self, pin, ptype):
        pass

    def _pin_type(self, pin):
        return ahio.PortType.Digital

    def _write(self, pin, value, pwm):
        pass

    def _read(self, pin):
        return 0

    def analog_references(self):
        return list(Driver.AnalogReferences)

    def _set_analog_reference(self, reference, pin):
        pass

    def _analog_reference(self, pin):
        return Driver.AnalogReferences.AR1

    def _set_pwm_frequency(self, frequency, pin):
        pass
