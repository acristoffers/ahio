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


class ahioDriverInfo(ahio.abstract_driver.AbstractahioDriverInfo):
    NAME = 'Modbus'
    AVAILABLE = True


class Driver(ahio.abstract_driver.AbstractDriver):
    _client = None
    _ports_direction = dict()
    _ports_type = dict()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._client:
            self._client.close()
            self._client = None
        pass

    def setup(
            self,
            configuration="ModbusSerialClient(method='rtu',port='/dev/cu.usbmodem14101',baudrate=9600)"
    ):
        """Start a Modbus server.

        The following classes are available with their respective named
        parameters:
        
        ModbusTcpClient
            host: The host to connect to (default 127.0.0.1)
            port: The modbus port to connect to (default 502)
            source_address: The source address tuple to bind to (default ('', 0))
            timeout: The timeout to use for this socket (default Defaults.Timeout)

        ModbusUdpClient
            host: The host to connect to (default 127.0.0.1)
            port: The modbus port to connect to (default 502)
            timeout: The timeout to use for this socket (default None)

        ModbusSerialClient
            method: The method to use for connection (asii, rtu, binary)
            port: The serial port to attach to
            stopbits: The number of stop bits to use (default 1)
            bytesize: The bytesize of the serial messages (default 8 bits)
            parity: Which kind of parity to use (default None)
            baudrate: The baud rate to use for the serial device
            timeout: The timeout between serial requests (default 3s)

        When configuring the ports, the following convention should be
        respected:
        
        portname: C1:13 -> Coil on device 1, address 13

        The letters can be:

        C = Coil
        I = Input
        R = Register
        H = Holding

        @arg configuration a string that instantiates one of those classes.

        @throw RuntimeError can't connect to Arduino
        """
        from pymodbus3.client.sync import ModbusSerialClient, ModbusUdpClient, ModbusTcpClient
        self._client = eval(configuration)
        self._client.connect()

    def available_pins(self):
        return []

    def _set_pin_direction(self, pin, direction):
        self._ports_direction[pin] = direction

    def _pin_direction(self, pin):
        return self._ports_direction[pin]

    def _set_pin_type(self, pin, ptype):
        self._ports_type[pin] = ptype

    def _pin_type(self, pin):
        return self._ports_type[pin]

    def _write(self, pin, value, pwm):
        ptype = pin[0].upper()
        unit, address = [int(i) for i in pin[1:].split(':')]
        func = self._client.write_register if ptype == 'R' else self._client.write_coil
        func(address, value, unit=unit)

    def _read(self, pin):
        ptype = pin[0].upper()
        unit, address = [int(i) for i in pin[1:].split(':')]
        func = {
            'C': self._client.read_coils,
            'I': self._client.read_discrete_inputs,
            'R': self._client.read_input_registers,
            'H': self._client.read_holding_registers
        }[ptype]
        ret = func(address, unit=unit)
        if hasattr(ret, 'bits'):
            return int(ret.bits[0])
        elif hasattr(ret, 'registers'):
            return float(ret.registers[0])
        else:
            return 0

    def analog_references(self):
        return []

    def _set_analog_reference(self, reference, pin):
        pass

    def _analog_reference(self, pin):
        return []

    def _set_pwm_frequency(self, frequency, pin):
        pass
