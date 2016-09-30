# Generic TCP I/O Protocol (GTIOP)

TCP protocol to control I/O ports.
Current version: 1.0

Every transmission ends with "\n". Every number transmitted must be an integer.

## Handshake

The server sends `HELLO 1.0`, where 1.0 is the protocol version.
Client answers `OK` if protocol is supported, `UNKNOWN` if not.

The server can try to handshake with lower protocol versions if handshake fails.

## Commands

### LISTPORTS

Lists all available I/O Ports.

*Answer:* `OK [obj,obj,...]` where obj is a JSON representation of the structure described in `ahio.abstract_driver.AbstractDriver.available_pins`. Here `id` must be an integer. For example:
```json
[{
    "id": 1,
    "name": "Pin 1",
    "analog": {
        "input": true,
        "output": false,
        "read_range": [
            0,
            1023
        ],
        "write_range": null
    },
    "digital": {
        "input": true,
        "output": true,
        "pwm": true
    }
}]
```

### SETDIRECTION PORT INPUT|OUTPUT

Sets the direction of `PORT` to `INPUT` or `OUTPUT`.

*Answer:* `OK` or `ERROR MSG`, where `MSG` is a message that describes the error that occurred.

### DIRECTION PORT

Returns the direction `PORT` is set to.

*Answer:* `OK INPUT|OUTPUT` or `ERROR MSG`

### SETTYPE PORT DIGITAL|ANALOG

Sets `PORT` to `DIGITAL` or `ANALOG`.

*Answer:* `OK` or `ERROR MSG`, where `MSG` is a message that describes the error that occurred.

### TYPE PORT

Gets the type of `PORT`.

*Answer:* `OK DIGITAL|ANALOG` or `ERROR MSG`

### WRITEDIGITAL PORT HIGH|LOW

Sets `PORT` output to `HIGH` or `LOW`.

*Answer:* `OK` or `ERROR MSG`, where `MSG` is a message that describes the error that occurred.

### WRITEANALOG PORT VALUE

Sets `PORT` output to `VALUE`, where `VALUE` is a number in range of `obj.analog.write_range`. See [`LISTPORTS`](#LISTPORTS).

*Answer:* `OK` or `ERROR MSG`, where `MSG` is a message that describes the error that occurred.

### WRITEPWM PORT VALUE

Sets `PORT` output to a PWM with dutycycle `VALUE`, where `VALUE` is a number between 0 and 1.

*Answer:* `OK` or `ERROR MSG`, where `MSG` is a message that describes the error that occurred.

### READDIGITAL PORT

Reads the tension in `PORT`.

*Answer:* `HIGH` or `LOW` as read on the port, or `ERROR MSG`, where `MSG` is a message that describes the error that occurred.

### READANALOG PORT

Reads the tension in `PORT`.

*Answer:* An integer in range of `obj.analog.read_range` (See [`LISTPORTS`](#LISTPORTS)), or `ERROR MSG`, where `MSG` is a message that describes the error that occurred.

### ANALOGREFERENCES

Returns the possible values for analog reference.

*Answer:* `OK V1 V2 V3`, where VN is a value that can be used as
analog reference.

### SETANALOGREFERENCE REFERENCE [PIN]

Sets the analog reference to `REFERENCE`. `REFERENCE` must be in the list returned by [`ANALOGREFERENCES`](#ANALOGREFERENCES). See `ahio.abstract_driver.AbstractDriver.set_analog_reference` for more information regarding this function.

*Answer:* `OK` or `ERROR MSG`, where `MSG` is a message that describes the error that occurred.

### ANALOGREFERENCE [PORT]

Returns the analog reference for `PORT` or the global analog reference case `PORT` is ommited.

*Answer:* `OK REFERECE` or `ERROR MSG`, where `MSG` is a message that describes the error that occurred.

### SETPWMFREQUENCY FREQUENCY [PORT]

Sets the PWM frequency of `PORT` to `FREQUENCY`. If `PORT` is omitted, sets it globally.

*Answer:* `OK` or `ERROR MSG`, where `MSG` is a message that describes the error that occurred.
