##IMPORTS
import board
from adafruit_bme280 import basic as adafruit_bme280
import matplotlib.pyplot as plt #for plotting
from matplotlib.ticker import AutoMinorLocator
import matplotlib.dates as mdates
import datetime
import time

i2c = board.I2C()  # uses I2C protocal on pi (pins 3&5)
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c) #sets up temp sensor in i2c config

#lists to store the values in
times = []
temps = []
humids = []
pressures = []

while True:
    times.append(datetime.datetime.utcnow())
    temps.append(bme280.temperature)
    humids.append(bme280.humidity)
    pressures.append(bme280.pressure)

    ###PLOTTING
    fig, ax = plt.subplots(1,3, figsize=(15,5))
    fig.suptitle("Hostname: superhans | Operating System: Raspbian GNU/Linux 11 (bullseye) | Location: Office 10 SLO")

    #plotting temps
    ax[0].plot_date(times,temps, color = 'royalblue')
    ax[0].set_xlabel('Time (UTC)')
    ax[0].set_ylabel(r'Temperature $(^oC)$')
    #produces 10 minor ticks between each tick on both axes
    ax[0].xaxis.set_minor_locator(AutoMinorLocator(10))
    ax[0].yaxis.set_minor_locator(AutoMinorLocator(10))

    #plotting humidity
    ax[1].plot_date(times,humids, color = 'coral')
    ax[1].set_xlabel('Time (UTC)')
    ax[1].set_ylabel(r'Humidity (%)')
    #produces 10 minor ticks between each tick on both axes
    ax[1].xaxis.set_minor_locator(AutoMinorLocator(10))
    ax[1].yaxis.set_minor_locator(AutoMinorLocator(10))

    #plotting pressure
    ax[2].plot_date(times,pressures, color = 'seagreen')
    ax[2].set_xlabel('Time (UTC)')
    ax[2].set_ylabel(r'Pressure (mbar)')
    #produces 10 minor ticks between each tick on both axes
    ax[2].xaxis.set_minor_locator(AutoMinorLocator(10))
    ax[2].yaxis.set_minor_locator(AutoMinorLocator(10))

    xfmt = mdates.DateFormatter('%H:%M:%S')
    for i in range(3):
        ax[i].xaxis.set_major_formatter(xfmt)


    plt.tight_layout()

    fig.savefig('meto-plots.png', dpi = 600)

    #clears the figure from memory
    fig.clear()
    plt.close(fig)

    time.sleep(600)
