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

"""@package ahio.abstract_driver
Contains abstract classes that should be implemented by drivers.
"""

import ahio


class AbstractahioDriverInfo(object):
    """Abstract class containing information about the driver.

    This class should be inherited and fully implemented by every driver. It
    contains information regarding the driver, as it's name and availability,
    for example.
    """
    NAME = 'Driver name'
    AVAILABLE = 'True if the driver is available, false otherwise'


class AbstractDriver(object):
    """Base class for drivers.

    Read the documentation carefully if you're developing a driver. Some
    functions require you to implement a private function with similar
    signature instead of the function itself.

    The driver can have a `setup` method with special signature to initialize
    itself using user provided parameters, like port to use for communication,
    for example. If no user parameters are needed, the initialization should
    occur in the `__init__` method.
    """

    _pin_mapping = {}
    _pin_lin = {}

    def available_pins(self):
        """Returns available pins.

        Returns a list of dictionaries indicating the available pins and it's
        capabilities. It should follow this format:
        \verbatim
        [ {
            'id': 1, # some value that represents this pin in your
                     # implementation.
                     # prefer numbers and Enums. This value will be used
                     # in `map_pin(a,p)`
            'name': 'Pin 1', # a name that can be shown to the user, if needed
            'analog': {
                'input': True, # if analog input is available
                'output': False, # if analog output is available
                'read_range': (0, 1023), # if input is supported, what is the
                                         # valid range (both inclusive)
                'write_range': (0, 5) # if output is supported, what is the
                                      #valid range (both inclusive)
            },
            'digital': {
                'input': True, # if digital input is available
                'output': True, # if digital output is available
                'pwm': True # if pwm generation is available
            }
        }]
        \endverbatim

        If you're developing a driver, you should override this function.

        @returns a list of dictionaries
        """
        raise NotImplementedMethod()

    def map_pin(self, abstract_pin_id, physical_pin_id):
        """Maps a pin number to a physical device pin.

        To make it easy to change drivers without having to refactor a lot of
        code, this library does not use the names set by the driver to identify
        a pin. This function will map a number, that will be used by other
        functions, to a physical pin represented by the drivers pin id. That
        way, if you need to use another pin or change the underlying driver
        completly, you only need to redo the mapping.

        If you're developing a driver, keep in mind that your driver will not
        know about this. The other functions will translate the mapped pin to
        your id before calling your function.

        @arg abstract_pin_id the id that will identify this pin in the
        other function calls. You can choose what you want.

        @arg physical_pin_id the id returned in the driver.
            See `AbstractDriver.available_pins`. Setting it to None removes the
            mapping.
        """
        if physical_pin_id:
            self._pin_mapping[abstract_pin_id] = physical_pin_id
        else:
            self._pin_mapping.pop(abstract_pin_id, None)

    def mapped_pins(self):
        """Returns a dictionary containing the mapped pins.

        Each key of the dictionary is the ID you set with map_pin, and each
        value is the driver-specific ID.

        @returns a dictionary of mapped pins
        """
        return self._pin_mapping

    def _linear_interpolation(self, x, imin, imax, omin, omax):
        return (imax * omin - imin * omax + x * (omax - omin)) / (imax - imin)

    def set_pin_interpolation(self,
                              pin,
                              read_min,
                              read_max,
                              write_min,
                              write_max):
        """Interpolates input and output values for `pin`.

        Changes the output and input of `AbstractDriver.read` and
        `AbstractDriver.write` functions to use a value in range
        (`read_min`, `read_max`) or (`write_min`, `write_max`) instead of the
        values returned by `available_pins` (analog only). The conversion is
        done using linear interpolation. If `read_min`, `read_max`, `write_min`
        and `write_max` are all None or don't form valid pairs (like, read_min
        has a value but read_max is None), the pin is deregistered. If you pass
        a pair but leave the other with None values, only one direction is
        registered.

        @arg pin pin id you've set using `AbstractDriver.map_pin`
        @arg read_min the min value for the linear interpolation of
             `AbstractDriver.read`.
        @arg read_max the max value for the linear interpolation of
             `AbstractDriver.read`.
        @arg write_min the min value for the linear interpolation of
             `AbstractDriver.write`.
        @arg write_max the max value for the linear interpolation of
             `AbstractDriver.write`.
        """
        if type(pin) is list:
            # I don't like breaking calls in multiple lines
            args = (read_min, read_max, write_min, write_max)
            for p in pin:
                self.set_pin_interpolation(p, *args)
            return

        valid_read = (read_min is not None and read_max is not None)
        valid_write = (write_min is not None and write_max is not None)

        if not valid_read and not valid_write:
            self._pin_lin.pop(pin, None)
            return

        pin_id = self._pin_mapping.get(pin, None)
        pins = [pin for pin in self.available_pins() if pin_id == pin['id']]
        read = pins[0]['analog']['read_range']
        write = pins[0]['analog']['write_range']
        valid_read = valid_read and read
        valid_write = valid_write and write
        self._pin_lin[pin] = {
            'read': (*read, read_min, read_max) if valid_read else None,
            'write': (write_min, write_max, *write) if valid_write else None
        }

    def set_pin_direction(self, pin, direction):
        """Sets pin `pin` to `direction`.

        The pin should support the requested mode. Calling this function
        on a unmapped pin does nothing. Calling it with a unsupported direction
        throws RuntimeError.

        If you're developing a driver, you should implement
        _set_pin_direction(self, pin, direction) where `pin` will be one of
        your internal IDs. If a pin is set to OUTPUT, put it on LOW state.

        @arg pin pin id you've set using `AbstractDriver.map_pin`
        @arg mode a value from `AbstractDriver.Direction`

        @throw KeyError if pin isn't mapped.
        @throw RuntimeError if direction is not supported by pin.
        """
        if type(pin) is list:
            for p in pin:
                self.set_pin_direction(p, direction)
            return

        pin_id = self._pin_mapping.get(pin, None)
        if pin_id and type(direction) is ahio.Direction:
            self._set_pin_direction(pin_id, direction)
        else:
            raise KeyError('Requested pin is not mapped: %s' % pin)

    def pin_direction(self, pin):
        """Gets the `ahio.Direction` this pin was set to.

        If you're developing a driver, implement _pin_direction(self, pin)

        @arg pin the pin you want to see the mode
        @returns the `ahio.Direction` the pin is set to

        @throw KeyError if pin isn't mapped.
        """
        if type(pin) is list:
            return [self.pin_direction(p) for p in pin]

        pin_id = self._pin_mapping.get(pin, None)
        if pin_id:
            return self._pin_direction(pin_id)
        else:
            raise KeyError('Requested pin is not mapped: %s' % pin)

    def set_pin_type(self, pin, ptype):
        """Sets pin `pin` to `type`.

        The pin should support the requested mode. Calling this function
        on a unmapped pin does nothing. Calling it with a unsupported mode
        throws RuntimeError.

        If you're developing a driver, you should implement
        _set_pin_type(self, pin, ptype) where `pin` will be one of your
        internal IDs. If a pin is set to OUTPUT, put it on LOW state.

        @arg pin pin id you've set using `AbstractDriver.map_pin`
        @arg mode a value from `AbstractDriver.PortType`

        @throw KeyError if pin isn't mapped.
        @throw RuntimeError if type is not supported by pin.
        """
        if type(pin) is list:
            for p in pin:
                self.set_pin_type(p, ptype)
            return

        pin_id = self._pin_mapping.get(pin, None)
        if type(ptype) is not ahio.PortType:
            raise KeyError('ptype must be of type ahio.PortType')
        elif pin_id:
            self._set_pin_type(pin_id, ptype)
        else:
            raise KeyError('Requested pin is not mapped: %s' % pin)

    def pin_type(self, pin):
        """Gets the `ahio.PortType` this pin was set to.

        If you're developing a driver, implement _pin_type(self, pin)

        @arg pin the pin you want to see the mode
        @returns the `ahio.PortType` the pin is set to

        @throw KeyError if pin isn't mapped.
        """
        if type(pin) is list:
            return [self.pin_type(p) for p in pin]

        pin_id = self._pin_mapping.get(pin, None)
        if pin_id:
            return self._pin_type(pin_id)
        else:
            raise KeyError('Requested pin is not mapped: %s' % pin)

    def write(self, pin, value, pwm=False):
        """Sets the output to the given value.

        Sets `pin` output to given value. If the pin is in INPUT mode, do
        nothing. If it's an analog pin, value should be in write_range.
        If it's not in the allowed range, it will be clamped. If pin is in
        digital mode, value can be `ahio.LogicValue` if `pwm` = False, or a
        number between 0 and 1 if `pwm` = True. If PWM is False, the pin will
        be set to HIGH or LOW, if `pwm` is True, a PWM wave with the given
        cycle will be created. If the pin does not support PWM and `pwm` is
        True, raise RuntimeError. The `pwm` argument should be ignored in case
        the pin is analog. If value is not valid for the given
        pwm/analog|digital combination, raise TypeError.

        If you're developing a driver, implement _write(self, pin, value, pwm)

        @arg pin the pin to write to
        @arg value the value to write on the pin
        @arg pwm wether the output should be a pwm wave

        @throw RuntimeError if the pin does not support PWM and `pwm` is True.
        @throw TypeError if value is not valid for this pin's mode and pwm
               value.
        @throw KeyError if pin isn't mapped.
        """
        if type(pin) is list:
            for p in pin:
                self.write(p, value, pwm)
            return

        if pwm and type(value) is not int and type(value) is not float:
            raise TypeError('pwm is set, but value is not a float or int')

        pin_id = self._pin_mapping.get(pin, None)
        if pin_id:
            lpin = self._pin_lin.get(pin, None)
            if lpin and type(lpin['write']) is tuple:
                write_range = lpin['write']
                value = self._linear_interpolation(value, *write_range)
            self._write(pin_id, value, pwm)
        else:
            raise KeyError('Requested pin is not mapped: %s' % pin)

    def read(self, pin):
        """Reads value from pin `pin`.

        Returns the value read from pin `pin`. If it's an analog pin, returns
        a number in analog.input_range. If it's digital, returns
        `ahio.LogicValue`.

        If you're developing a driver, implement _read(self, pin)

        @arg pin the pin to read from
        @returns the value read from the pin

        @throw KeyError if pin isn't mapped.
        """
        if type(pin) is list:
            return [self.read(p) for p in pin]

        pin_id = self._pin_mapping.get(pin, None)
        if pin_id:
            value = self._read(pin_id)
            lpin = self._pin_lin.get(pin, None)
            if lpin and type(lpin['read']) is tuple:
                read_range = lpin['read']
                value = self._linear_interpolation(value, *read_range)
            return value
        else:
            raise KeyError('Requested pin is not mapped: %s' % pin)

    def analog_references(self):
        """Possible values for analog reference.

        If you're developing a driver, override this function.

        @returns a list of values that can be passed to set_analog_reference or
            returned from analog_reference(). Very driver specific.
        """
        raise NotImplementedMethod()

    def set_analog_reference(self, reference, pin=None):
        """Sets the analog reference to `reference`

        If the driver supports per pin reference setting, set pin to the
        desired reference. If not, passing None means set to all, which is the
        default in most hardware. If only per pin reference is supported and
        pin is None, raise RuntimeError.

        If you're developing a driver, implement
        _set_analog_reference(self, reference, pin). Raise RuntimeError if pin
        was set but is not supported by the platform.

        @arg reference the value that describes the analog reference. See
            `AbstractDriver.analog_references`
        @arg pin if the the driver supports it, the pin that will use
            `reference` as reference. None for all.

        @throw RuntimeError if pin is None on a per pin only hardware, or if
            it's a valid pin on a global only analog reference hardware.
        @throw KeyError if pin isn't mapped.
        """
        if pin is None:
            self._set_analog_reference(reference, None)
        else:
            pin_id = self._pin_mapping.get(pin, None)
            if pin_id:
                self._set_analog_reference(reference, pin_id)
            else:
                raise KeyError('Requested pin is not mapped: %s' % pin)

    def analog_reference(self, pin=None):
        """Returns the analog reference.

        If the driver supports per pin analog reference setting, returns the
        reference for pin `pin`. If pin is None, returns the global analog
        reference. If only per pin reference is supported and pin is None,
        raise RuntimeError.

        If you're developing a driver, implement _analog_reference(self, pin)

        @arg pin if the the driver supports it, the pin that will use
            `reference` as reference. None for all.

        @returns the reference used for pin

        @throw RuntimeError if pin is None on a per pin only hardware, or if
            it's a valid pin on a global only analog reference hardware.
        @throw KeyError if pin isn't mapped.
        """
        if pin is None:
            return self._analog_reference(None)
        else:
            pin_id = self._pin_mapping.get(pin, None)
            if pin_id:
                return self._analog_reference(pin_id)
            else:
                raise KeyError('Requested pin is not mapped: %s' % pin)

    def set_pwm_frequency(self, frequency, pin=None):
        """Sets PWM frequency, if supported by hardware

        If the driver supports per pin frequency setting, set pin to the
        desired frequency. If not, passing None means set to all. If only per
        pin frequency is supported and pin is None, raise RuntimeError.

        If you're developing a driver, implement
        _set_pwm_frequency(self, frequency, pin). Raise RuntimeError if pin
        was set but is not supported by the platform.

        @arg frequency pwm frequency to be set, in Hz
        @arg pin if the the driver supports it, the pin that will use
            `frequency` as pwm frequency. None for all/global.

        @throw RuntimeError if pin is None on a per pin only hardware, or if
            it's a valid pin on a global only hardware.
        @throw KeyError if pin isn't mapped.
        """
        if pin is None:
            self._set_pwm_frequency(frequency, None)
        else:
            pin_id = self._pin_mapping.get(pin, None)
            if pin_id:
                self._set_pwm_frequency(frequency, pin_id)
            else:
                raise KeyError('Requested pin is not mapped: %s' % pin)
