import datetime as dt
from skyfield.api import N,S,E,W, wgs84, load, utc
from skyfield import almanac
import time
import json
import glob
import cv2 as cv
import numpy as np
from tqdm import tqdm
from exif import Image

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

imgs = glob.glob("/media/george/Work/skyWATCH/20220407/*.jpg")
temps = glob.glob('dome-templates/hf**.jpg') #loads in templates

for i in imgs:

    #read image metadata
    with open(i, "rb") as photo:
        image = Image(photo)

    date = dt.datetime.strptime(image['datetime'], '%Y:%m:%d %H:%M:%S') #converts date into datetime object
    date=date.replace(tzinfo=utc) #adds utc time zone to datetime object - may need to chnage this
    tnow = ts.from_datetime(date) #saves time as skyfield time object

    tnowdt = tnow.utc_datetime().strftime("%Y-%m-%d %H:%M:%S") #string version
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


    ## DETECT IF DOME IS OPEN OR CLOSED ##
    # NEW METHOD #

    img = cv.imread(i,0)

    #highlight dome fetures
    img = np.invert(cv.equalizeHist(img)).clip(min=150)
    #histogram flattener normalises the brightness of the images

    img2 = img.copy()

    img = img2.copy()
    method = eval('cv.TM_CCOEFF')

    results = []
    locs = []
    limsx = [[2884,2984],[774,874]]
    limsy = [[167,267],[576,676]]

    for j in range(2): # 2 templates to match (either can match for +ve result)
        template = cv.imread(temps[j],0)

        # Apply template Matching
        res = cv.matchTemplate(img,template,method)
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)
        locs.append(max_loc)

        #checks if predicted location of template in image is within x pixels of the true position (if not then its likely the dome is open)
        if (max_loc[0] > limsx[j][0]) & (max_loc[0] < limsx[j][1]):
            if (max_loc[1] > limsy[j][0]) & (max_loc[1] < limsy[j][1]):
                results.append(True)
            else:
                results.append(False)
        else:
            results.append(False)


    if (results[0] or results[1]) == True:
        result = "Closed"
    else:
        result = "Open"


    #construct dict of these values to be turned into JSON
    values = {"time":tnowdt,
    "location":{"name":name,"latitude":roqueN,"longitude":roqueE,"elevation":roqueELV},
              "period of the day":mode,
              "sun":{"altitude":round(alt.degrees,7)},
              "moon":{"altitude":round(malt.degrees,7),"phase":round(mphase,7),"illumination":round(mill,7)},
              "dome-status": result,
              "image":{"name":i[-26:],"exposure time":image["exposure_time"], "width":image["image_width"], "height":image["image_height"]}
             }

    #saves json
    with open(f'out/{tnow.utc_datetime().strftime("%Y%m%d_%H%M%S")}.json', 'w') as fp:
        json.dump(values, fp,indent=4)
