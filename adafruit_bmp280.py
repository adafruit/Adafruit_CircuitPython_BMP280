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

CircuitPython driver from BMP280 Temperature and Barometic Pressure sensor

* Author(s): ladyada
"""
import time, math
from micropython import const
try:
    import struct
except ImportError:
    import ustruct as struct

#    I2C ADDRESS/BITS/SETTINGS
#    -----------------------------------------------------------------------
_BMP280_CHIPID  = const(0x58)

_BMP280_REGISTER_CHIPID  = const(0xD0)
_BMP280_REGISTER_DIG_T1  = const(0x88)
"""
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
"""
_BMP280_REGISTER_SOFTRESET  = const(0xE0)
_BMP280_REGISTER_STATUS = const(0xF3)
_BMP280_REGISTER_CONTROL = const(0xF4)
_BMP280_REGISTER_CONFIG = const(0xF5)
_BMP280_REGISTER_PRESSUREDATA  = const(0xF7)
_BMP280_REGISTER_TEMPDATA = const(0xFA)

class Adafruit_BMP280:
    """Base BMP280 object. Use `Adafruit_BMP280_I2C` or `Adafruit_BMP280_SPI` instead of this. This checks the BMP280 was found, reads the coefficients and enables the sensor for continuous reads"""
    def __init__(self):
        # Check device ID.
        id = self._read_byte(_BMP280_REGISTER_CHIPID)
        if _BMP280_CHIPID != id:
            raise RuntimeError('Failed to find BMP280! Chip ID 0x%x' % id)
        self._read_coefficients()
        self.seaLevelhPa = 1013.25
        """Pressure in hectoPascals at sea level. Used to calibrate `altitude`."""

    @property
    def temperature(self):
        """The compensated temperature in degrees celsius."""
        # perform one measurement in high res, forced mode
        self._write_register_byte(_BMP280_REGISTER_CONTROL, 0xFE)

        # Wait for conversion to complete
        while (self._read_byte(_BMP280_REGISTER_STATUS) & 0x08):
            time.sleep(0.002)
        # lowest 4 bits get dropped
        UT = self._read24(_BMP280_REGISTER_TEMPDATA) / 16
        #print("raw temp: ", UT)

        var1 = (UT / 16384.0 - self.dig_T1 / 1024.0) * self.dig_T2
        var2 = ((UT / 131072.0 - self.dig_T1 / 8192.0) * (
            UT / 131072.0 - self.dig_T1 / 8192.0)) * self.dig_T3
        self.t_fine = int(var1 + var2)
        #print("t_fine: ", self.t_fine)

        temp = (var1 + var2) / 5120.0
        return temp

    @property
    def pressure(self):
        """The compensated pressure in hectoPascals."""
        self.temperature  # force read (gets temp & pressure)

        # lowest 4 bits get dropped
        adc = self._read24(_BMP280_REGISTER_PRESSUREDATA) / 16
        var1 = float(self.t_fine) / 2.0 - 64000.0
        var2 = var1 * var1 * self.dig_P6 / 32768.0
        var2 = var2 + var1 * self.dig_P5 * 2.0
        var2 = var2 / 4.0 + self.dig_P4 * 65536.0
        var1 = (self.dig_P3 * var1 * var1 / 524288.0 + self.dig_P2 * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self.dig_P1
        if var1 == 0:
            return 0
        p = 1048576.0 - adc
        p = ((p - var2 / 4096.0) * 6250.0) / var1
        var1 = self.dig_P9 * p * p / 2147483648.0
        var2 = p * self.dig_P8 / 32768.0
        p = p + (var1 + var2 + self.dig_P7) / 16.0
        return p / 100

    @property
    def altitude(self):
        """The altitude based on the sea level pressure (`seaLevelhPa`) - which you must enter ahead of time)"""
        p = self.pressure # in Si units for hPascal
        return 44330 * (1.0 - math.pow(p / self.seaLevelhPa, 0.1903));

    ####################### Internal helpers ################################
    def _read_coefficients(self):
        """Read & save the calibration coefficients"""
        coeff = self._read_register(_BMP280_REGISTER_DIG_T1, 24)
        coeff = list(struct.unpack('<HhhHhhhhhhhh', bytes(coeff)))
        coeff = [float(i) for i in coeff]
        self.dig_T1, self.dig_T2, self.dig_T3 , self.dig_P1, self.dig_P2, self.dig_P3, self.dig_P4, self.dig_P5, self.dig_P6, self.dig_P7, self.dig_P8, self.dig_P9 = coeff
        #print("%d %d %d" % (self.dig_T1, self.dig_T2, self.dig_T3))
        #print("%d %d %d" % (self.dig_P1, self.dig_P2, self.dig_P3))
        #print("%d %d %d" % (self.dig_P4, self.dig_P5, self.dig_P6))
        #print("%d %d %d" % (self.dig_P7, self.dig_P8, self.dig_P9))

    def _read_byte(self, register):
        """Read a byte register value and return it"""
        return self._read_register(register, 1)[0]

    def _read24(self, register):
        """Read an unsigned 24-bit value as a floating point and return it."""
        ret = 0.0
        for b in self._read_register(register, 3):
            ret *= 256.0
            ret += float(b & 0xFF)
        return ret


class Adafruit_BMP280_I2C(Adafruit_BMP280):
    """Driver for I2C connected BMP280. Default address is 0x77 but another address can be passed in as an argument"""
    def __init__(self, i2c, address=0x77):
        import adafruit_bus_device.i2c_device as i2c_device
        self._i2c = i2c_device.I2CDevice(i2c, address)
        super().__init__()

    def _read_register(self, register, length):
        """Low level register reading over I2C, returns a list of values"""
        with self._i2c as i2c:
            i2c.write(bytes([register & 0xFF]))
            result = bytearray(length)
            i2c.readinto(result)
            #print("$%02X => %s" % (register, [hex(i) for i in result]))
            return result

    def _write_register_byte(self, register, value):
        """Low level register writing over I2C, writes one 8-bit value"""
        with self._i2c as i2c:
            i2c.write(bytes([register & 0xFF, value & 0xFF]))
            #print("$%02X <= 0x%02X" % (register, value))

class Adafruit_BMP280_SPI(Adafruit_BMP280):
    """Driver for SPI connected BMP280. Default clock rate is 100000 but can be changed with 'baudrate'"""
    def __init__(self, spi, cs, baudrate=100000):
        import adafruit_bus_device.spi_device as spi_device
        self._spi = spi_device.SPIDevice(spi, cs, baudrate=baudrate)
        super().__init__()

    def _read_register(self, register, length):
        """Low level register reading over SPI, returns a list of values"""
        register = (register | 0x80) & 0xFF  # Read single, bit 7 high.
        with self._spi as spi:
            spi.write(bytearray([register]))
            result = bytearray(length)
            spi.readinto(result)
            #print("$%02X => %s" % (register, [hex(i) for i in result]))
            return result

    def _write_register_byte(self, register, value):
        """Low level register writing over SPI, writes one 8-bit value"""
        register &= 0x7F  # Write, bit 7 low.
        with self._spi as spi:
            spi.write(bytes([register, value & 0xFF]))
