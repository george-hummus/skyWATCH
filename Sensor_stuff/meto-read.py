import board
from adafruit_bme280 import basic as adafruit_bme280
i2c = board.I2C()  # uses I2C protocal on pi (pins 3&5)
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c) #sets up temp sensor in i2c config

with open('meto-info.txt', 'w') as file:
    # Writing meto readings to a text file
    file.write("| Hostname: superhans | Operating System: Raspbian GNU/Linux 11 (bullseye) | Location: Office 10 SLO |\n")
    file.write("\n")
    file.write("Temperature: %0.1f C\n" % bme280.temperature)
    file.write("Humidity: %0.1f %%\n" % bme280.humidity)
    file.write("Pressure: %0.1f mbar\n" % bme280.pressure) #hPa and mbar are the same
