#!/usr/bin/env python3


import loki
import time

arduino = loki.new_driver('Arduino')

print(loki.list_available_drivers())
print(arduino)

arduino.setup('/dev/tty.usbmodem1421')

arduino.map_pin(1, arduino.Pins.D1)
arduino.map_pin(2, arduino.Pins.D2)

arduino.set_pin_direction([1, 2], loki.Direction.Output)
arduino.write([1, 2], loki.LogicValue.High)
arduino.set_pin_direction([1, 2], loki.Direction.Input)
print(arduino.read([1, 2]))
