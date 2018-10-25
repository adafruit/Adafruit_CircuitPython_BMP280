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
import math
import time
try:
    import struct
except ImportError:
    import ustruct as struct

from micropython import const

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BMP280.git"

#    I2C ADDRESS/BITS/SETTINGS
#    -----------------------------------------------------------------------
_CHIP_ID = const(0x58)

_REGISTER_CHIPID = const(0xD0)
_REGISTER_DIG_T1 = const(0x88)
# _REGISTER_DIG_T2 = const(0x8A)
# _REGISTER_DIG_T3 = const(0x8C)
# _REGISTER_DIG_P1 = const(0x8E)
# _REGISTER_DIG_P2 = const(0x90)
# _REGISTER_DIG_P3 = const(0x92)
# _REGISTER_DIG_P4 = const(0x94)
# _REGISTER_DIG_P5 = const(0x96)
# _REGISTER_DIG_P6 = const(0x98)
# _REGISTER_DIG_P7 = const(0x9A)
# _REGISTER_DIG_P8 = const(0x9C)
# _REGISTER_DIG_P9 = const(0x9E)
_REGISTER_SOFTRESET = const(0xE0)
_REGISTER_STATUS = const(0xF3)
_REGISTER_CONTROL = const(0xF4)
_REGISTER_CONFIG = const(0xF5)
_REGISTER_PRESSUREDATA = const(0xF7)
_REGISTER_TEMPDATA = const(0xFA)

class Adafruit_BMP280: # pylint: disable=invalid-name
    """Base BMP280 object. Use `Adafruit_BMP280_I2C` or `Adafruit_BMP280_SPI` instead of this. This
       checks the BMP280 was found, reads the coefficients and enables the sensor for continuous
       reads"""
    def __init__(self):
        # Check device ID.
        chip_id = self._read_byte(_REGISTER_CHIPID)
        if _CHIP_ID != chip_id:
            raise RuntimeError('Failed to find BMP280! Chip ID 0x%x' % chip_id)
        self._read_coefficients()
        self.sea_level_pressure = 1013.25
        """Pressure in hectoPascals at sea level. Used to calibrate `altitude`."""

    def _read(self):
        """Returns a tuple for temperature and pressure."""
        # perform one measurement in high res, forced mode
        self._write_register_byte(_REGISTER_CONTROL, 0xFE)

        # Wait for conversion to complete
        while self._read_byte(_REGISTER_STATUS) & 0x08:
            time.sleep(0.002)
        # lowest 4 bits get dropped
        UT = self._read24(_REGISTER_TEMPDATA) / 16
        #print("raw temp: ", UT)

        var1 = (UT / 16384.0 - self._temp_calib[0] / 1024.0) * self._temp_calib[1]
        var2 = ((UT / 131072.0 - self._temp_calib[0] / 8192.0) * (
            UT / 131072.0 - self._temp_calib[0] / 8192.0)) * self._temp_calib[2]
        #print("t_fine: ", self.t_fine)
        t_fine = int(var1 + var2)
        temperature = t_fine / 5120.0

        adc = self._read24(_REGISTER_PRESSUREDATA) / 16
        var1 = float(t_fine) / 2.0 - 64000.0
        var2 = var1 * var1 * self._pressure_calib[5] / 32768.0
        var2 = var2 + var1 * self._pressure_calib[4] * 2.0
        var2 = var2 / 4.0 + self._pressure_calib[3] * 65536.0
        var1 = (self._pressure_calib[2] * var1 * var1 / 524288.0 +
                self._pressure_calib[1] * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self._pressure_calib[0]
        if var1 == 0:
            return 0
        p = 1048576.0 - adc
        p = ((p - var2 / 4096.0) * 6250.0) / var1
        var1 = self._pressure_calib[8] * p * p / 2147483648.0
        var2 = p * self._pressure_calib[7] / 32768.0
        p = p + (var1 + var2 + self._pressure_calib[6]) / 16.0
        pressure = p / 100
        return (temperature, pressure)

    @property
    def temperature(self):
        """The compensated temperature in degrees celsius."""
        return self._read()[0]

    @property
    def pressure(self):
        """The compensated pressure in hectoPascals."""
        return self._read()[1]

    @property
    def altitude(self):
        """The altitude based on the sea level pressure (`sea_level_pressure`) - which you must
           enter ahead of time)"""
        p = self.pressure # in Si units for hPascal
        return 44330 * (1.0 - math.pow(p / self.sea_level_pressure, 0.1903))

    ####################### Internal helpers ################################
    def _read_coefficients(self):
        """Read & save the calibration coefficients"""
        coeff = self._read_register(_REGISTER_DIG_T1, 24)
        coeff = list(struct.unpack('<HhhHhhhhhhhh', bytes(coeff)))
        coeff = [float(i) for i in coeff]
        # The temp_calib lines up with DIG_T# registers.
        self._temp_calib = coeff[:3]
        self._pressure_calib = coeff[3:]
        # print("%d %d %d" % (self._temp_calib[0], self._temp_calib[1], self._temp_calib[2]))
        # print("%d %d %d" % (self._pressure_calib[0], self._pressure_calib[1],
        #                     self._pressure_calib[2]))
        # print("%d %d %d" % (self._pressure_calib[3], self._pressure_calib[4],
        #                     self._pressure_calib[5]))
        # print("%d %d %d" % (self._pressure_calib[6], self._pressure_calib[7],
        #                     self._pressure_calib[8]))

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

    def _read_register(self, register, length):
        """Low level register reading, not implemented in base class"""
        raise NotImplementedError()

    def _write_register_byte(self, register, value):
        """Low level register writing, not implemented in base class"""
        raise NotImplementedError()

class Adafruit_BMP280_I2C(Adafruit_BMP280): # pylint: disable=invalid-name
    """Driver for I2C connected BMP280. Default address is 0x77 but another address can be passed
       in as an argument"""
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
    """Driver for SPI connected BMP280. Default clock rate is 100000 but can be changed with
      'baudrate'"""
    def __init__(self, spi, cs, baudrate=100000):
        import adafruit_bus_device.spi_device as spi_device
        self._spi = spi_device.SPIDevice(spi, cs, baudrate=baudrate)
        super().__init__()

    def _read_register(self, register, length):
        """Low level register reading over SPI, returns a list of values"""
        register = (register | 0x80) & 0xFF  # Read single, bit 7 high.
        with self._spi as spi:
            # pylint: disable=no-member
            spi.write(bytearray([register]))
            result = bytearray(length)
            spi.readinto(result)
            #print("$%02X => %s" % (register, [hex(i) for i in result]))
            return result

    def _write_register_byte(self, register, value):
        """Low level register writing over SPI, writes one 8-bit value"""
        register &= 0x7F  # Write, bit 7 low.
        with self._spi as spi:
            # pylint: disable=no-member
            spi.write(bytes([register, value & 0xFF]))
