import board
import busio
import time
from adafruit_bmp280 import adafruit_bmp280

i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)

while not i2c.try_lock():    pass
print("I2C addresses found:", [hex(i) for i in i2c.scan()])
i2c.unlock()
    
# Create library object on our I2C port
bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)

while True:
    print("\nTemperature: %0.1f C" % bmp280.temperature)
    print("Pressure: %0.1f hPa" % bmp280.pressure)
    print("Altitude = %0.2f meters" % bmp280.altitude)
    time.sleep(2)
