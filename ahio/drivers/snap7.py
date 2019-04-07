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

try:
    import snap7
except Exception:
    ahioDriverInfo.AVAILABLE = False


def retry_on_job_pending(func):
    def f(*args, **kargs):
        exception = None
        for _ in range(3):
            try:
                return func(*args, **kargs)
            except Snap7Exception as e:
                exception = e
                if 'Job pending' not in str(exception):
                    raise exception
        else:
            raise exception

    return f


class ahioDriverInfo(ahio.abstract_driver.AbstractahioDriverInfo):
    NAME = 'snap7'
    AVAILABLE = True


class Driver(ahio.abstract_driver.AbstractDriver):
    _client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._client:
            self._client.disconnect()
        self._client = None

    def setup(self, address, rack=0, slot=1, port=102):
        """Connects to a Siemens S7 PLC.

        Connects to a Siemens S7 using the Snap7 library.
        See [the snap7 documentation](http://snap7.sourceforge.net/) for
        supported models and more details.

        It's not currently possible to query the device for available pins,
        so `available_pins()` returns an empty list. Instead, you should use
        `map_pin()` to map to a Merker, Input or Output in the PLC. The
        internal id you should use is a string following this format:
        '[DMQI][XBWD][0-9]+.?[0-9]*' where:

        * [DMQI]: D for DB, M for Merker, Q for Output, I for Input
        * [XBWD]: X for bit, B for byte, W for word, D for dword
        * [0-9]+: Address of the resource
        * [0-9]*: Bit of the address (type X only, ignored in others)

        For example: 'IB100' will read a byte from an input at address 100 and
        'MX50.2' will read/write bit 2 of the Merker at address 50. It's not
        allowed to write to inputs (I), but you can read/write Outpus, DBs and
        Merkers. If it's disallowed by the PLC, an exception will be thrown by
        python-snap7 library.

        For this library to work, it might be needed to change some settings
        in the PLC itself. See
        [the snap7 documentation](http://snap7.sourceforge.net/) for more
        information. You also need to put the PLC in RUN mode. Not however that
        having a Ladder program downloaded, running and modifying variables
        will probably interfere with inputs and outputs, so put it in RUN mode,
        but preferably without a downloaded program.

        @arg address IP address of the module.
        @arg rack rack where the module is installed.
        @arg slot slot in the rack where the module is installed.
        @arg port port the PLC is listenning to.

        @throw RuntimeError if something went wrong
        @throw any exception thrown by `snap7`'s methods.
        """
        rack = int(rack)
        slot = int(slot)
        port = int(port)
        address = str(address)
        self._client = snap7.client.Client()
        self._client.connect(address, rack, slot, port)

    def available_pins(self):
        return []

    def _set_pin_direction(self, pin, direction):
        d = self._pin_direction(pin)
        if direction != d and not (type(d) is list and direction in d):
            raise RuntimeError('Port %s does not support this Direction' % pin)

    def _pin_direction(self, pin):
        return {
            'D': [ahio.Direction.Input, ahio.Direction.Output],
            'M': [ahio.Direction.Input, ahio.Direction.Output],
            'Q': ahio.Direction.Output,
            'I': ahio.Direction.Input
        }[pin[0].upper()]

    def _set_pin_type(self, pin, ptype):
        raise RuntimeError('Hardware does not support changing the pin type')

    def _pin_type(self, pin):
        raise RuntimeError('Hardware does not support querying the pin type')

    def _write(self, pin, value, pwm):
        if pwm:
            raise RuntimeError('Pin does not support PWM')
        if self._pin_direction(pin) == ahio.Direction.Input:
            raise RuntimeError('Can not write to Input')
        mem = self._parse_port_name(pin)
        value = {
            ahio.LogicValue.High: 1,
            ahio.LogicValue.Low: 0
        }.get(value, value)
        self._set_memory(mem, value)

    def _read(self, pin):
        mem = self._parse_port_name(pin)
        value = self._get_memory(mem)
        if mem[1] == 'X':
            return {
                0: ahio.LogicValue.Low,
                1: ahio.LogicValue.High
            }.get(value, value)
        else:
            return value

    def analog_references(self):
        return []

    def _set_analog_reference(self, reference, pin):
        raise RuntimeError('Hardware does not support setting analog ref')

    def _analog_reference(self, pin):
        pass

    def _set_pwm_frequency(self, frequency, pin):
        raise RuntimeError(
            'Setting PWM frequency is not supported by hardware')

    def _parse_port_name(self, s):
        s = s.upper()
        area = {
            'D': snap7.snap7types.S7AreaDB,
            'M': snap7.snap7types.S7AreaMK,
            'Q': snap7.snap7types.S7AreaPA,
            'I': snap7.snap7types.S7AreaPE
        }[s[0]]
        length = {'X': 1, 'B': 1, 'W': 2, 'D': 4}[s[1]]
        start = int(s.split('.')[0][2:])
        bit = int(s.split('.')[1]) if s[1] == 'X' else None
        dtype = {
            'X': {
                'get': lambda m: snap7.util.get_bool(m, 0, bit),
                'set': lambda m, v: snap7.util.set_bool(m, 0, bit, v)
            },
            'B': {
                'get': lambda m: snap7.util.get_int(m, 0),
                'set': lambda m, v: snap7.util.set_int(m, 0, v)
            },
            'W': {
                'get': lambda m: snap7.util.get_int(m, 0),
                'set': lambda m, v: snap7.util.set_int(m, 0, v)
            },
            'D': {
                'get': lambda m: snap7.util.get_dword(m, 0),
                'set': lambda m, v: snap7.util.set_dword(m, 0, v)
            }
        }[s[1]]
        return (area, dtype, start, length)

    @retry_on_job_pending
    def _get_memory(self, mem):
        m = self._client.read_area(mem[0], 0, mem[2], mem[3])
        return mem[1]['get'](m)

    @retry_on_job_pending
    def _set_memory(self, mem, value):
        m = self._client.read_area(mem[0], 0, mem[2], mem[3])
        mem[1]['set'](m, value)
        self._client.write_area(mem[0], 0, mem[2], m)
