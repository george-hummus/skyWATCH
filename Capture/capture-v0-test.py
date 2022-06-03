'''
Version 0 of the new capture script for the skyWATCH camera.
What it does:
- calculates whether it should open depending on the time of day
- if in day time mode:
    - checks every 15mins if sun is less than 5 degrees above horizon
    - if it is then changes to night-time mode and makes directory to save images to
    - if not it stays in day-time mode
- if in night-time mode
    - takes an expsoure
    - checks if it is still night-time mode (if not switches to day-time; if so continues)
    - calculates time of day (depends on sun's altitude)
    - calculates the moon's altitude, phase, and illumination
    - reads images metadata (exposure time, height, width, etc.,)
    - detects if the dome is open (if it is sleeps for 15 mins before enxt exposure)
    - saves all info to JSON file with same name as image and in same directory

To-do:
- test the base script works on laptop with fake capture (this!)
- make version 0.1 which has a mode for dome open and closed (takes image that is overwitten if dome is still closed)
- make version 0.1.1 for use on rapsberry pi with real capture (on old pi-cam api)
- chnage the exposure time on the fly with each new image for best all-sky image
- make option to load in your own templates for the dome detect (or it could make ones for you?)
- make version for the new pi-cam api

Author: George Hume
2022
'''

## IMPORTS ##
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
import os

## SETUP ##
if len(glob.glob("setup.json")) == 0: #if no setup file then you'll be prompted to create one
    print("Welcome to first time setup of skyWATCH camera!")
    devname = input("Name of device: ")
    locname = input("Name of the location: ")
    lat = input("Latitude of location (in decimal degrees): ")
    long = input("Longitude of location (in decimal degrees): ")
    elv = input("Elevation above sea-level of location (in meteres): ")
    prams = {"device_name":devname,"location":locname,"latitude":float(lat),"longitude":float(long),"elevation":float(elv)}
    with open('setup.json', 'w') as fp: #saves setupfile as a json
        json.dump(prams, fp,indent=4)
else: #otherwise it reads the setup file
    with open('setup.json', 'r') as f:
        prams = json.load(f)

temps = ['dome-templates/hf-002.jpg','dome-templates/hf-001.jpg'] #loads in templates for dome detection

eph = load('de421.bsp') #loads ephemerides
ts = load.timescale() #loads time scale

#sets up sun and moon plus position on earth
earth, sun, moon = eph['earth'],eph['sun'],eph['moon']
ORM = earth + wgs84.latlon(prams["latitude"] * N, prams["longitude"] * E, elevation_m=prams["elevation"])

active = False #boolean to check if cam should start exposing - starts on False

## start time to speed up testing ##
startT = dt.datetime(2022,6,3,20,0,0,tzinfo=utc)
i=0

print("setup complete")

## OPERATION LOOP ##
while True:

    ## DAY-TIME MODE ##
    while active == False: #loop to check the time of day
        #tnow = ts.now() #saves time now

        print("false")
        tnow=ts.from_datetime(startT+dt.timedelta(minutes=i*30)) ##
        i+=1 #increases time by 30mins with each cycle - only for testing

        astro = ORM.at(tnow).observe(sun)
        app = astro.apparent()
        alt, az, distance = app.altaz() #finds the altitude of the sun
        if alt.degrees < 5:
            datenow = tnow.utc_strftime("%Y%m%d")
            path = f"out/{datenow}"
            os.mkdir(path) #makes directory for images on new night
            active = True #sets active status to True is altitude of sun is below 5 degs
        else:
            #time.sleep(900) #checks every 15mins if it is nighttime
            time.sleep(10) #10sec sleep for testing


    ## NIGHT-TIME MODE ##
    while active == True:
        #need the time first
        #tnow = ts.now() #saves time now

        print("true")
        tnow=ts.from_datetime(startT+dt.timedelta(minutes=i*30)) ##
        i+=1 #increases time by 30mins with each cycle - only for testing

        tnowstr = tnow.utc_strftime("%Y-%m-%d %H:%M:%S") #string version
        tnowfn = tnow.utc_strftime("%Y%m%d_%H%M%S") #filename version

        #capture image
        devname = prams["device_name"]
        img_name = f"{tnowfn}_{devname}.jpg"
        # capture(f"{path}/{img_name}")

        astro = ORM.at(tnow).observe(sun)
        app = astro.apparent()
        alt, az, distance = app.altaz()
        print(tnowstr)
        print(alt.degrees)

        #checks if it is nighttime otherwise go to day-time mode
        if alt.degrees > 5:
            active = False #sets active status to False if altitude of sun is above 5 degs

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

        #read image metadata
        #with open(f'{path}/{img_name}', "rb") as photo:
        with open("test.jpg", "rb") as photo:
            meta = Image(photo)

        ## DETECT IF DOME IS OPEN OR CLOSED ##
        #img = cv.imread(f'{path}/{img_name}',0)
        img = cv.imread('test.jpg',0)

        #highlight dome fetures
        img = np.invert(cv.equalizeHist(img)).clip(min=150)
        #histogram flattener normalises the brightness of the images

        img2 = img.copy()

        img = img2.copy()
        method = eval('cv.TM_CCOEFF')

        results = []
        limsx = [[2884,2984],[774,874]]
        limsy = [[167,267],[576,676]]

        for j in range(2): # 2 templates to match (either can match for +ve result)
            template = cv.imread(temps[j],0)

            # Apply template Matching
            res = cv.matchTemplate(img,template,method)
            min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)

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
        values = {"device":prams["device_name"],"time":tnowstr,
        "image":{"name":img_name,"exposure time":meta["exposure_time"], "width":meta["image_width"], "height":meta["image_height"]},
        "location":{"name":prams["location"],"latitude":prams["latitude"],"longitude":prams["longitude"],"elevation":prams["elevation"]},
                  "period of the day":mode,
                  "sun":{"altitude":round(alt.degrees,7)},
                  "moon":{"altitude":round(malt.degrees,7),"phase":round(mphase,7),"illumination":round(mill,7)},
                  "dome-status": result
                 }

        #saves json
        with open(f'{path}/{img_name[:-4]}.json', 'w') as fp:
            json.dump(values, fp,indent=4)

        if (results[0] or results[1]) == True:
            #time.sleep(900) #checks every 15mins if it is nighttime
            time.sleep(10) #10sec sleep for testing
