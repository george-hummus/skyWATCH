##IMPORTS
import board
from adafruit_bme280 import basic as adafruit_bme280
import matplotlib.pyplot as plt #for plotting
from matplotlib.ticker import AutoMinorLocator
import matplotlib.dates as mdates
import datetime
import time
import csv

i2c = board.I2C()  # uses I2C protocal on pi (pins 3&5)
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c) #sets up temp sensor in i2c config

try:
    #import data
    with open('meto_out/data.csv', newline='') as f:
        reader = csv.reader(f)
        data = list(reader)

    temps = data[1]
    humids = data[2]
    pressures = data[3]
except:
    #empty list if the start
    temps = []
    humids = []
    pressures = []

#appending new valules
temps.append(bme280.temperature)
humids.append(bme280.humidity)
pressures.append(bme280.pressure)

#setting up times
times = []
time_now = datetime.datetime.utcnow()
step = len(temps)
for j in range(step):
    c_time = (10*step) - ((j+1)*10) # change in time to get to 1st 2nd 3rd times etc., from now
    time = time_now - datetime.timedelta(minutes=c_time) #time to be added to list
    times.append(time) #appending to list


#SETTING UP FIG + animation
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

xfmt = mdates.DateFormatter('%H:%M')
for i in range(3):
    ax[i].xaxis.set_major_formatter(xfmt)


plt.tight_layout()

fig.savefig('meto_out/meto-plots.png', dpi = 600)

#clears fig to save memory
fig.clear()
plt.close(fig)

#saves data out for next run
with open('meto_out/data.csv', 'w') as f:

    write = csv.writer(f)

    write.writerow(times)
    write.writerow(temps)
    write.writerow(humids)
    write.writerow(pressures)
