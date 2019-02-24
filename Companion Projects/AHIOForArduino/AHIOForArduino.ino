void handshake();

void setup()
{
    Serial.begin(115200);
    handshake();
}

void waitForSerial()
{
    while ( Serial.available() == 0 ) {
    }
}

byte AnalogReference = DEFAULT;
byte convertAnalogReference()
{
    switch ( AnalogReference ) {
        case DEFAULT:
            return 0;

//        case INTERNAL:
//            return 1;

        case EXTERNAL:
            return 2;

        default:
            return -1;
    }
}

byte convertAnalogReference(uint8_t reference)
{
    switch ( reference ) {
        case 0:
            return DEFAULT;

//        case 1:
//            return INTERNAL;

        case 2:
            return EXTERNAL;
    }
}

void loop()
{
    if ( Serial.available() > 0 ) {
        if ( Serial.read() == 0x02 ) {
            waitForSerial();
            byte command = Serial.read();

            switch ( command ) {
                case 0xC1: // get analog reference
                    Serial.write( convertAnalogReference() );
                    break;

                case 0xC2: // set analog reference
                {
                    waitForSerial();
                    byte reference = Serial.read();
                    AnalogReference = convertAnalogReference(reference);
                    analogReference(AnalogReference);
                    break;
                }

                case 0xC3: // set mode
                {
                    waitForSerial();
                    byte pin = Serial.read();
                    waitForSerial();
                    byte dir = Serial.read();
                    pinMode(pin, dir ? INPUT : OUTPUT);
                    break;
                }

                case 0xC4: // get mode
                {
                    waitForSerial();
                    byte             pin  = Serial.read();
                    uint8_t          bit  = digitalPinToBitMask(pin);
                    uint8_t          port = digitalPinToPort(pin);
                    volatile uint8_t *reg = portModeRegister(port);
                    Serial.write( (*reg & bit) ? 0 : 1 );
                    break;
                }

                case 0xC5: // read digital
                {
                    waitForSerial();
                    byte pin = Serial.read();
                    Serial.write( digitalRead(pin) );
                    break;
                }

                case 0xC6: // read analog
                {
                    waitForSerial();
                    byte     pin = Serial.read();
                    uint16_t val = analogRead(pin);
                    Serial.write(  (val >> 8) & 0xFF );
                    Serial.write(val & 0xFF);
                    break;
                }

                case 0xC7: // write digital
                {
                    waitForSerial();
                    byte pin = Serial.read();
                    waitForSerial();
                    byte val = Serial.read();
                    digitalWrite(pin, val);
                    break;
                }

                case 0xC8: // write pwm
                {
                    waitForSerial();
                    byte pin = Serial.read();
                    waitForSerial();
                    byte val = Serial.read();
                    analogWrite(pin, val);
                    break;
                }

                default:
                    break;
            }
        }
    }
}

void handshake()
{
    while ( true ) {
        if ( Serial.available() > 0 ) {
            byte b = Serial.read();
            if ( b == 0x01 ) {
                Serial.write(0x06);
                return;
            }
        }
    }
}
