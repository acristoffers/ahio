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

import json
import socket
from enum import Enum


class ahioDriverInfo(ahio.abstract_driver.AbstractahioDriverInfo):
    NAME = 'GenericTCPIO'
    AVAILABLE = True


class Driver(ahio.abstract_driver.AbstractDriver):
    _socket = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._socket:
            self._socket.send(b'QUIT\n')
            self._socket.close()

    def setup(self, address, port):
        """Connects to server at `address`:`port`.

        Connects to a TCP server listening at `address`:`port` that implements
        the protocol described in the file "Generic TCP I:O Protocol.md"

        @arg address IP or address to connect to.
        @arg port port to connect to.

        @throw RuntimeError if connection was successiful but protocol isn't
               supported.
        @throw any exception thrown by `socket.socket`'s methods.
        """
        address = str(address)
        port = int(port)
        self._socket = socket.socket()
        self._socket.connect((address, port))
        self._socket.send(b'HELLO 1.0\n')
        with self._socket.makefile() as f:
            if f.readline().strip() != 'OK':
                raise RuntimeError('Protocol not supported')

    def __clamp(self, value, min, max):
        return sorted((min, value, max))[1]

    def available_pins(self):
        self._socket.send(b'LISTPORTS\n')
        with self._socket.makefile() as f:
            answer = f.readline()
        if answer.startswith('OK'):
            return json.loads(answer[3:])
        elif answer.startswith('ERROR'):
            raise RuntimeError(answer[6:])
        else:
            raise RuntimeError('Unknown response')

    def _set_pin_direction(self, pin, direction):
        direction = 'INPUT' if direction == ahio.Direction.Input else 'OUTPUT'
        command = ('SETDIRECTION %s %s\n' % (pin, direction)).encode('utf8')
        self._socket.send(command)
        with self._socket.makefile() as f:
            answer = f.readline()
        if answer.startswith('OK'):
            return None
        elif answer.startswith('ERROR'):
            raise RuntimeError(answer[6:])
        else:
            raise RuntimeError('Unknown response')

    def _pin_direction(self, pin):
        command = ('DIRECTION %s\n' % pin).encode('utf8')
        self._socket.send(command)
        with self._socket.makefile() as f:
            answer = f.readline()
        if answer.startswith('OK'):
            direction = answer[3:].strip()
            d = ahio.Direction
            return d.Input if direction == 'INPUT' else d.Output
        elif answer.startswith('ERROR'):
            raise RuntimeError(answer[6:])
        else:
            raise RuntimeError('Unknown response')

    def _set_pin_type(self, pin, ptype):
        ptype = 'DIGITAL' if ptype == ahio.PortType.Digital else 'ANALOG'
        command = ('SETTYPE %s %s\n' % (pin, ptype)).encode('utf8')
        self._socket.send(command)
        with self._socket.makefile() as f:
            answer = f.readline()
        if answer.startswith('OK'):
            return None
        elif answer.startswith('ERROR'):
            raise RuntimeError(answer[6:])
        else:
            raise RuntimeError('Unknown response')

    def _pin_type(self, pin):
        command = ('TYPE %s\n' % pin).encode('utf8')
        self._socket.send(command)
        with self._socket.makefile() as f:
            answer = f.readline()
        if answer.startswith('OK'):
            ptype = answer[3:].strip()
            pt = ahio.PortType
            return pt.Digital if ptype == 'DIGITAL' else pt.Analog
        elif answer.startswith('ERROR'):
            raise RuntimeError(answer[6:])
        else:
            raise RuntimeError('Unknown response')

    def _find_port_info(self, pin):
        ps = [p for p in self.available_pins() if p['id'] == pin]
        if ps:
            return ps[0]
        else:
            return None

    def _write(self, pin, value, pwm):
        if self._pin_direction(pin) == ahio.Direction.Input:
            return None
        pin_info = self._find_port_info(pin)
        if self._pin_type(pin) == ahio.PortType.Digital:
            if not pin_info['digital']['output']:
                raise RuntimeError('Pin does not support digital output')
            if pwm:
                if not pin_info['digital']['pwm']:
                    raise RuntimeError('Pin does not support PWM')
                value = self.__clamp(value, 0, 1)
                command = ('WRITEPWM %s %s\n' % (pin, value)).encode('utf8')
            else:
                value = 'HIGH' if value == ahio.LogicValue.High else 'LOW'
                command = ('WRITEDIGITAL %s %s\n' %
                           (pin, value)).encode('utf8')
        else:
            if not pin_info['analog']['output']:
                raise RuntimeError('Pin does not support analog output')
            l = pin_info['analog']['write_range']
            value = self.__clamp(value, l[0], l[1])
            command = ('WRITEANALOG %s %s\n' % (pin, value)).encode('utf8')
        self._socket.send(command)
        with self._socket.makefile() as f:
            answer = f.readline()
        if answer.startswith('OK'):
            return None
        elif answer.startswith('ERROR'):
            raise RuntimeError(answer[6:])
        else:
            raise RuntimeError('Unknown response')

    def _read(self, pin):
        pin_info = self._find_port_info(pin)
        pin_type = self._pin_type(pin)
        if pin_info['digital']['input'] and pin_type == ahio.PortType.Digital:
            da = ahio.PortType.Digital
            command = ('READDIGITAL %s\n' % pin).encode('utf8')
        elif pin_info['analog']['input'] and pin_type == ahio.PortType.Analog:
            da = ahio.PortType.Analog
            command = ('READANALOG %s\n' % pin).encode('utf8')
        else:
            raise RuntimeError('Pin does not support input or is not set up')
        self._socket.send(command)
        with self._socket.makefile() as f:
            answer = f.readline()
        if answer.startswith('OK'):
            value = answer[3:].strip()
            if da == ahio.PortType.Digital:
                lv = ahio.LogicValue
                return lv.High if value == 'HIGH' else lv.Low
            else:
                return int(value)
        elif answer.startswith('ERROR'):
            raise RuntimeError(answer[6:])
        else:
            raise RuntimeError('Unknown response')

    def analog_references(self):
        self._socket.send(b'ANALOGREFERENCES\n')
        with self._socket.makefile() as f:
            answer = f.readline()
        if answer.startswith('OK'):
            __, *opts = answer.strip().split(' ')
            return opts
        elif answer.startswith('ERROR'):
            raise RuntimeError(answer[6:])
        else:
            raise RuntimeError('Unknown response')

    def _set_analog_reference(self, reference, pin):
        if pin:
            command = ('SETANALOGREFERENCE %s %s\n' % (reference, pin))
        else:
            command = ('SETANALOGREFERENCE %s\n' % reference)
        self._socket.send(command.encode('utf8'))
        with self._socket.makefile() as f:
            answer = f.readline()
        if answer.startswith('OK'):
            return
        elif answer.startswith('ERROR'):
            raise RuntimeError(answer[6:])
        else:
            raise RuntimeError('Unknown response')

    def _analog_reference(self, pin):
        if pin:
            command = 'ANALOGREFERENCE %s\n' % pin
        else:
            command = 'ANALOGREFERENCE\n'
        self._socket.send(command.encode('utf8'))
        with self._socket.makefile() as f:
            answer = f.readline()
        if answer.startswith('OK'):
            return answer.strip().split(' ')[1]
        elif answer.startswith('ERROR'):
            raise RuntimeError(answer[6:])
        else:
            raise RuntimeError('Unknown response')

    def _set_pwm_frequency(self, frequency, pin):
        if pin:
            command = 'SETPWMFREQUENCY %s %s\n' % (frequency, pin)
        else:
            command = 'SETPWMFREQUENCY %s\n' % frequency
        self._socket.send(command.encode('utf8'))
        with self._socket.makefile() as f:
            answer = f.readline()
        if answer.startswith('OK'):
            return
        elif answer.startswith('ERROR'):
            raise RuntimeError(answer[6:])
        else:
            raise RuntimeError('Unknown response')
