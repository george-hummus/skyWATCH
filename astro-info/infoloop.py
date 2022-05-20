import datetime as dt
from skyfield.api import N,S,E,W, wgs84, load
from skyfield import almanac
import time
import json

#location of roque
name = "observatory roque de la muchachos"
roqueN = 28.6468866
roqueE = -17.7742491
roqueELV = 2326

eph = load('de421.bsp') #loads ephemerides
ts = load.timescale() #loads time scale

#sets up sun and moon plus position on earth
earth, sun, moon = eph['earth'],eph['sun'],eph['moon']
ORM = earth + wgs84.latlon(roqueN * N, roqueE * E, elevation_m=roqueELV)

while True:
    tnow = ts.now() #saves time now
    tnowdt = tnow.utc_datetime().strftime("%Y-%m-%d %H:%M:%S") #datetime version
    astro = ORM.at(tnow).observe(sun)
    app = astro.apparent()
    alt, az, distance = app.altaz()

    #calculate the time of day
    if alt.degrees > 0:
        mode = "day time"
    elif (0>alt.degrees>-6):
        mode = "civil twilight"
    elif (-6>alt.degrees>-12):
        mode = "nautical twilight"
    elif (-12>alt.degrees>-18):
        mode = "astronomical twilight"
    else:
        mode = "dark time"

    #calculate moon's alt, phase, and illumination
    mastro = ORM.at(tnow).observe(moon)
    mapp = mastro.apparent()
    malt, maz, mdst = mapp.altaz()
    mphase = almanac.moon_phase(eph, tnow).degrees
    mill = almanac.fraction_illuminated(eph,"moon",tnow)

    #construct dict of these values to be turned into JSON
    values = {"time":tnowdt,
    "location":{"name":name,"latitude":roqueN,"longitude":roqueE,"elevation":roqueELV},
              "period of the day":mode,
              "sun":{"altitude":round(alt.degrees,7)},
              "moon":{"altitude":round(malt.degrees,7),"phase":round(mphase,7),"illumination":round(mill,7)}
             }

    #saves json
    with open(f'out/{tnow.utc_datetime().strftime("%Y%m%d_%H%M%S")}.json', 'w') as fp:
        json.dump(values, fp,indent=4)

    time.sleep(1800)
