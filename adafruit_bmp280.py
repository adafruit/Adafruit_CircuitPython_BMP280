# The MIT License (MIT)
#
# Copyright (c) 2017 ladyada for Adafruit Industries
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
"""
`adafruit_bmp280`
====================================================

CircuitPython driver from BMP280 sensor

* Author(s): ladyada
"""
import time, math
try:
    import struct
except ImportError:
    import ustruct as struct

#    I2C ADDRESS/BITS/SETTINGS
#    -----------------------------------------------------------------------
BMP280_ADDRESS = const(0x77)
BMP280_CHIPID  = const(0x58)

BMP280_REGISTER_CHIPID  = const(0xD0)
BMP280_REGISTER_DIG_T1  = const(0x88)
BMP280_REGISTER_DIG_T2  = const(0x8A)
BMP280_REGISTER_DIG_T3 = const(0x8C)
BMP280_REGISTER_DIG_P1  = const(0x8E)
BMP280_REGISTER_DIG_P2  = const(0x90)
BMP280_REGISTER_DIG_P3 = const(0x92)
BMP280_REGISTER_DIG_P4 = const(0x94)
BMP280_REGISTER_DIG_P5  = const(0x96)
BMP280_REGISTER_DIG_P6  = const(0x98)
BMP280_REGISTER_DIG_P7 = const(0x9A)
BMP280_REGISTER_DIG_P8 = const(0x9C)
BMP280_REGISTER_DIG_P9  = const(0x9E)
BMP280_REGISTER_VERSION  = const(0xD1)
BMP280_REGISTER_SOFTRESET  = const(0xE0)
BMP280_REGISTER_CAL26  = const(0xE1)  # R calibration stored in 0xE1-0xF0
BMP280_REGISTER_STATUS = const(0xF3)
BMP280_REGISTER_CONTROL = const(0xF4)
BMP280_REGISTER_CONFIG = const(0xF5)
BMP280_REGISTER_PRESSUREDATA  = const(0xF7)
BMP280_REGISTER_TEMPDATA = const(0xFA)

class Adafruit_BMP280:
    def __init__(self):
        # Check device ID.
        if BMP280_CHIPID != self._read_byte(BMP280_REGISTER_CHIPID):
            raise RuntimeError('Failed to find BMP280!')
        self._read_coefficients()
        self._write_byte(BMP280_REGISTER_CONTROL, 0x3F);
        self.seaLevelhPa = 1013.25

    @property
    def temperature(self):
        """Gets the compensated temperature in degrees celsius."""
        # Wait for conversion to complete
        while (self._read_byte(BMP280_REGISTER_STATUS) & 0x08):    
            time.sleep(0.002)
        UT = self._read24(BMP280_REGISTER_TEMPDATA) / 16  # lowest 4 bits get dropped
        #print("raw temp: ", UT)

        var1 = (UT / 16384.0 - float(self.dig_T1) / 1024.0) * float(self.dig_T2)
        var2 = ((UT / 131072.0 - float(self.dig_T1) / 8192.0) * (
            UT / 131072.0 - float(self.dig_T1) / 8192.0)) * float(self.dig_T3)
        self.t_fine = int(var1 + var2)
        #print("t_fine: ", self.t_fine)
        
        temp = (var1 + var2) / 5120.0
        return temp

    @property
    def pressure(self):
        """Gets the compensated pressure in Pascals."""
        self.temperature  # force read
        
        adc = self._read24(BMP280_REGISTER_PRESSUREDATA) / 16  # lowest 4 bits get dropped
        var1 = float(self.t_fine) / 2.0 - 64000.0
        var2 = var1 * var1 * float(self.dig_P6) / 32768.0
        var2 = var2 + var1 * float(self.dig_P5) * 2.0
        var2 = var2 / 4.0 + float(self.dig_P4) * 65536.0
        var1 = (float(self.dig_P3) * var1 * var1 / 524288.0 + float(self.dig_P2) * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * float(self.dig_P1)
        if var1 == 0:
            return 0
        p = 1048576.0 - adc
        p = ((p - var2 / 4096.0) * 6250.0) / var1
        var1 = float(self.dig_P9) * p * p / 2147483648.0
        var2 = p * float(self.dig_P8) / 32768.0
        p = p + (var1 + var2 + float(self.dig_P7)) / 16.0
        return p

    @property
    def altitude(self):
        p = self.pressure / 100.0 # in Si units for Pascal
        return 44330 * (1.0 - math.pow(p / self.seaLevelhPa, 0.1903));

    def _read_coefficients(self):
        """Read & save the calibration coefficients"""
        self.dig_T1 = self._read16_LE(BMP280_REGISTER_DIG_T1);
        self.dig_T2 = self._readS16_LE(BMP280_REGISTER_DIG_T2);
        self.dig_T3 = self._readS16_LE(BMP280_REGISTER_DIG_T3);
        self.dig_P1 = self._read16_LE(BMP280_REGISTER_DIG_P1);
        self.dig_P2 = self._readS16_LE(BMP280_REGISTER_DIG_P2);
        self.dig_P3 = self._readS16_LE(BMP280_REGISTER_DIG_P3);
        self.dig_P4 = self._readS16_LE(BMP280_REGISTER_DIG_P4);
        self.dig_P5 = self._readS16_LE(BMP280_REGISTER_DIG_P5);
        self.dig_P6 = self._readS16_LE(BMP280_REGISTER_DIG_P6);
        self.dig_P7 = self._readS16_LE(BMP280_REGISTER_DIG_P7);
        self.dig_P8 = self._readS16_LE(BMP280_REGISTER_DIG_P8);
        self.dig_P9 = self._readS16_LE(BMP280_REGISTER_DIG_P9);
        #print("%d %d %d" % (self.dig_T1, self.dig_T2, self.dig_T3))
        #print("%d %d %d" % (self.dig_P1, self.dig_P2, self.dig_P3))
        #print("%d %d %d" % (self.dig_P4, self.dig_P5, self.dig_P6))
        #print("%d %d %d" % (self.dig_P7, self.dig_P8, self.dig_P9))

    def _write_byte(self, register, value):
        # Write a byte register value
        return self._write_register_byte(register, value)
     
    def _read_byte(self, register):
        # Read a byte register value and return it.
        return self._read_register(register, 1)[0]

    def _read16_LE(self, register):
        # Read an unsigned 16-bit value and return it.
        t = self._read_register(register, 2)
        return (t[0] & 0xFF) | ((t[1] & 0xFF) << 8)

    def _readS16_LE(self, register):
        # Read an unsigned 16-bit value and return it.
        x = self._read16_LE(register)
        if x > 0x7FFF:
            x -= 0x10000
        return x

    def _read24(self, register):
        # Read an unsigned 24-bit value as a floating point and return it.
        ret = 0.0
        for b in self._read_register(register, 3)[:3]:
            ret *= 256.0
            ret += float(b & 0xFF)
        return ret
    
class Adafruit_BMP280_I2C(Adafruit_BMP280):
    def __init__(self, i2c, address=BMP280_ADDRESS):
        import adafruit_bus_device.i2c_device as i2c_device
        self._i2c = i2c_device.I2CDevice(i2c, address)
        self._buffer = bytearray(3)
        super().__init__()

    def _read_register(self, register, length):
        self._buffer[0] = register & 0xFF
        with self._i2c as i2c:
            i2c.write(self._buffer, start=0, end=1)
            i2c.read_into(self._buffer, start=0, end=length)
            #print("$%02X => %s" % (register, [hex(i) for i in self._buffer[:length]]))
            return self._buffer

    def _write_register_byte(self, register, value):
        self._buffer[0] = register & 0xFF
        self._buffer[1] = value & 0xFF
        with self._i2c as i2c:
            i2c.write(self._buffer, start=0, end=2)
            #print("$%02X <= 0x%02X" % (register, value))
