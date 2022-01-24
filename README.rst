Introduction
============

.. image:: https://readthedocs.org/projects/adafruit-circuitpython-bmp280/badge/?version=latest
    :target: https://docs.circuitpython.org/projects/bmp280/en/latest/
    :alt: Documentation Status

.. image :: https://img.shields.io/discord/327254708534116352.svg
    :target: https://adafru.it/discord
    :alt: Discord

.. image:: https://github.com/adafruit/Adafruit_CircuitPython_BMP280/workflows/Build%20CI/badge.svg
    :target: https://github.com/adafruit/Adafruit_CircuitPython_BMP280/actions/
    :alt: Build Status

CircuitPython driver from BMP280 Temperature and Barometic Pressure sensor

Installation and Dependencies
=============================

This driver depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_
* `Bus Device <https://github.com/adafruit/Adafruit_CircuitPython_BusDevice>`_

Please ensure all dependencies are available on the CircuitPython filesystem.
This is easily achieved by downloading
`the Adafruit library and driver bundle <https://github.com/adafruit/Adafruit_CircuitPython_Bundle>`_.

Installing from PyPI
--------------------

On supported GNU/Linux systems like the Raspberry Pi, you can install the driver
`from PyPI <https://pypi.org/project/adafruit-circuitpython-bmp280/>`_. To install
for the current user:

.. code-block:: shell

    pip3 install adafruit-circuitpython-bmp280

To install system-wide (this may be required in some cases):

.. code-block:: shell

    sudo pip3 install adafruit-circuitpython-bmp280

To install in a virtual environment in your current project:

.. code-block:: shell

    mkdir project-name && cd project-name
    python3 -m venv .env
    source .env/bin/activate
    pip3 install adafruit-circuitpython-bmp280

Usage Example
=============

.. code-block:: python

    import time
    import board
    # import digitalio # For use with SPI
    import adafruit_bmp280

    # Create sensor object, communicating over the board's default I2C bus
    i2c = board.I2C()   # uses board.SCL and board.SDA
    bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)

    # OR Create sensor object, communicating over the board's default SPI bus
    # spi = board.SPI()
    # bmp_cs = digitalio.DigitalInOut(board.D10)
    # bmp280 = adafruit_bmp280.Adafruit_BMP280_SPI(spi, bmp_cs)

    # change this to match the location's pressure (hPa) at sea level
    bmp280.sea_level_pressure = 1013.25

    while True:
        print("\nTemperature: %0.1f C" % bmp280.temperature)
        print("Pressure: %0.1f hPa" % bmp280.pressure)
        print("Altitude = %0.2f meters" % bmp280.altitude)
        time.sleep(2)

Documentation
=============

API documentation for this library can be found on `Read the Docs <https://docs.circuitpython.org/projects/bmp280/en/latest/>`_.

Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/adafruit/Adafruit_CircuitPython_bmp280/blob/main/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.

Documentation
=============

For information on building library documentation, please check out `this guide <https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/sharing-our-docs-on-readthedocs#sphinx-5-1>`_.Travis will. This is a good way to
locally verify it will pass.
