import loki.abstract_driver

import serial
import time
from enum import Enum


class LokiDriverInfo(loki.abstract_driver.AbstractLokiDriverInfo):
    NAME = 'Arduino'
    AVAILABLE = True


class Driver(loki.abstract_driver.AbstractDriver):
    _serial = None

    Pins = Enum(
        'Pins', 'D0 D1 D2 D3 D4 D5 D6 D7 D8 D9 D10 D11 D12 D13 A1 A2 A3 A4 A5')

    AnalogReferences = Enum('AnalogReferences', 'Default Internal External')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def setup(self, port):
        """Connects to an Arduino UNO on serial port `port`.

        @throw RuntimeError can't connect to Arduino
        """
        # timeout is used by all I/O operations
        self._serial = serial.Serial(port, 115200, timeout=2)
        time.sleep(2)  # time to Arduino reset

        if not self._serial.is_open:
            raise RuntimeError('Could not connect to Arduino')

        self._serial.write(b'\x01')

        if self._serial.read() != b'\x06':
            raise RuntimeError('Could not connect to Arduino')

        ps = [p for p in self.available_pins() if p['digital']['output']]
        for pin in ps:
            self._set_pin_direction(pin['id'], loki.Direction.Output)

    def __clamp(self, value, min, max):
        return sorted((min, value, max))[1]

    def __create_pin_info(self, pid, pwm=False):
        is_analog = pid.name.startswith('A')
        obj = {
            'id': pid,
            'name': None,
            'analog': {
                'input': is_analog,
                'output': False,
                'read_range': (0, 1023) if is_analog else None,
                'write_range': None
            },
            'digital': {
                'input': not is_analog,
                'output': not is_analog,
                'pwm': not is_analog and pwm
            }
        }
        if is_analog:
            obj['name'] = 'Analog %s' % (pid.value - 14)
        else:
            obj['name'] = 'Digital %s' % (pid.value - 1)
        return obj

    def available_pins(self):
        pins = [p for p in Driver.Pins]
        pwms = [self.__create_pin_info(pin, True)
                for pin in pins
                if (pin.value - 1) in [3, 5, 6, 9, 10, 11]]
        pins = [self.__create_pin_info(pin)
                for pin in pins
                if (pin.value - 1) not in [3, 5, 6, 9, 10, 11]]
        return sorted(pwms + pins, key=lambda pin: pin['id'].value)

    def _set_pin_direction(self, pin, direction):
        if pin.name.startswith('A') and direction == loki.Direction.Output:
            raise RuntimeError('Analog pins can only be used as Input')
        if direction == loki.Direction.Input:
            self._serial.write(
                b'\x02\xC3' + bytes({pin.value - 1}) + bytes({1}))
        else:
            self._serial.write(
                b'\x02\xC3' + bytes({pin.value - 1}) + bytes({0}))
            self._serial.write(
                b'\x02\xC7' + bytes({pin.value - 1}) + bytes({0}))

    def _pin_direction(self, pin):
        self._serial.write(b'\x02\xC4' + bytes({pin.value - 1}))
        direction = self._serial.read()
        if direction == b'\x01':
            return loki.Direction.Input
        elif direction == b'\x00':
            return loki.Direction.Output
        else:
            return None

    def _set_pin_type(self, pin, ptype):
        is_analog = pin.name.startswith('A')
        if is_analog and ptype == loki.PortType.Digital:
            raise RuntimeError('Analog pin can not be set as digital')
        if not is_analog and ptype == loki.PortType.Analog:
            raise RuntimeError('Digtal pin can not be set as analog')

    def _pin_type(self, pin):
        return loki.PortType.Analog if pin.name.startswith('A') else loki.PortType.Digital

    def _write(self, pin, value, pwm):
        if self._pin_direction(pin) == loki.Direction.Input:
            return None
        if pin.name.startswith('D'):
            if pwm:
                if (pin.value - 1) not in [3, 5, 6, 9, 10, 11]:
                    raise RuntimeError('Pin does not support PWM output')
                if type(value) == int or type(value) == float:
                    value = int(255 * self.__clamp(float(value), 0.0, 1.0))
                    command = b'\x02\xC8' + bytes({pin.value - 1})
                    arg = bytes({value})
                    self._serial.write(command + arg)
                else:
                    raise TypeError(
                        'Value should be a float or int between 0 and 1')
            else:
                if type(value) == loki.LogicValue:
                    value = 1 if value == loki.LogicValue.High else 0
                    command = b'\x02\xC7' + bytes({pin.value - 1})
                    arg = bytes({value})
                    self._serial.write(command + arg)
                else:
                    raise TypeError('Value should be of type loki.LogicValue')
        else:
            raise RuntimeError('Can not write to analog pin')

    def _read(self, pin):
        if pin.name.startswith('D'):
            self._serial.write(b'\x02\xC5' + bytes({pin.value - 1}))
            value = self._serial.read()
            return loki.LogicValue.High if value == b'\x01' else loki.LogicValue.Low
        else:
            self._serial.write(b'\x02\xC6' + bytes({pin.value - 14}))
            value_high = self._serial.read()
            value_low = self._serial.read()
            return (value_high[0] << 8) | value_low[0]

    def analog_references(self):
        return [r for r in Driver.AnalogReferences]

    def _set_analog_reference(self, reference, pin):
        if pin != None:
            raise RuntimeError('Per pin analog reference is not supported')
        self._serial.write(b'\x02\xC2' + bytes({reference.value - 1}))

    def _analog_reference(self, pin):
        self._serial.write(b'\x02\xC1')
        reference = self._serial.read()[0]
        return [Driver.AnalogReferences.Default,
                Driver.AnalogReferences.Internal,
                Driver.AnalogReferences.External][reference]

    def _set_pwm_frequency(self, frequency, pin):
        raise RuntimeError(
            'Setting PWM frequency is not supported by hardware')
