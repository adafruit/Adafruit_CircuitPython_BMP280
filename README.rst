
Introduction
============

.. image:: https://readthedocs.org/projects/adafruit-circuitpython-bmp280/badge/?version=latest
    :target: https://circuitpython.readthedocs.io/projects/bmp280/en/latest/
    :alt: Documentation Status

.. image :: https://img.shields.io/discord/327254708534116352.svg
    :target: https://discord.gg/nBQh6qu
    :alt: Discord

CircuitPython driver from BMP280 Temperature and Barometic Pressure sensor

Dependencies
=============
This driver depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_
* `Bus Device <https://github.com/adafruit/Adafruit_CircuitPython_BusDevice>`_

Please ensure all dependencies are available on the CircuitPython filesystem.
This is easily achieved by downloading
`the Adafruit library and driver bundle <https://github.com/adafruit/Adafruit_CircuitPython_Bundle>`_.

Usage Example
=============


.. code-block:: python

	import board
	import digitalio
	import busio
	import time
	from adafruit_bmp280 import adafruit_bmp280

	# Create library object using our Bus I2C port
	i2c = busio.I2C(board.SCL, board.SDA)
	bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)

	# OR create library object using our Bus SPI port
	#spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
	#bmp_cs = digitalio.DigitalInOut(board.D10)
	#bmp280 = adafruit_bmp280.Adafruit_BMP280_SPI(spi, bmp_cs)

	# change this to match the location's pressure (hPa) at sea level
	bmp280.seaLevelhPa = 1013.25

	while True:
	    print("\nTemperature: %0.1f C" % bmp280.temperature)
	    print("Pressure: %0.1f hPa" % bmp280.pressure)
	    print("Altitude = %0.2f meters" % bmp280.altitude)
	    time.sleep(2)

Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/adafruit/Adafruit_CircuitPython_bmp280/blob/master/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.

API Reference
=============

.. toctree::
   :maxdepth: 2

   api
