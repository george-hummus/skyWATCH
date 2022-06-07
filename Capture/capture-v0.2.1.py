'''
Version 0.2.1 of the new capture script for the skyWATCH camera.
What it does:
- calculates whether it should open depending on the time of day
- if in day time mode:
    - checks every 15mins if sun is less than 5 degrees above horizon
    - if it is then changes to night-time mode and makes directory to save images to
    - if not it stays in day-time mode
- if in night-time mode
    - takes an expsoure using picamera library
    - checks if it is still night-time mode (if not switches to day-time; if so continues)
    - calculates time of day (depends on sun's altitude)
    - calculates the moon's altitude, phase, and illumination
    - reads images metadata (exposure time, height, width, etc.,)
    - detects if the dome is open (if it is sleeps for 15 mins before enxt exposure)
    - saves all info to JSON file with same name as image and in same directory
    - has a mode for dome open and closed (constantly takes an image when dome is closed to check if it has reopened, but this image is overwitten each time)
- creates a log for the night where it notes down key info

To-do:
- change the exposure time on the fly with each new image for best all-sky image
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
from picamera import PiCamera

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

devname = prams["device_name"]

eph = load('de421.bsp') #loads ephemerides
ts = load.timescale() #loads time scale

#sets up sun and moon plus position on earth
earth, sun, moon = eph['earth'],eph['sun'],eph['moon']
ORM = earth + wgs84.latlon(prams["latitude"] * N, prams["longitude"] * E, elevation_m=prams["elevation"])

active = False #boolean to check if cam should start exposing - starts on False
domestatus = False #boolean to check if the dome is open or not (false means open)

### define functions to be used in script ###

def sun_alt(t):
    #finds the altitude of the sun
    astro = ORM.at(t).observe(sun)
    app = astro.apparent()
    alt, az, distance = app.altaz()
    return alt.degrees

def timeoday(alt):
    if alt > 0:
        mode = "day time"
    elif (0>alt>-6):
        mode = "civil twilight"
    elif (-6>alt>-12):
        mode = "nautical twilight"
    elif (-12>alt>-18):
        mode = "astronomical twilight"
    else:
        mode = "dark time"
    return mode

def moon_props(t):
    #calculate moon's alt, phase, and illumination
    mastro = ORM.at(t).observe(moon)
    mapp = mastro.apparent()
    malt, maz, mdst = mapp.altaz()
    mphase = almanac.moon_phase(eph, t)
    mill = almanac.fraction_illuminated(eph,"moon",t)
    return malt.degrees,mphase.degrees,mill

def dome_detect(fname):
    ## DETECT IF DOME IS OPEN OR CLOSED ##
    img = cv.imread(fname,0)

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

    domestatus = (results[0] or results[1])

    return domestatus

## Inialising Camera ##
camera = PiCamera()

## OPERATION LOOP ##
while True:

    ## DAY-TIME MODE ##
    while active == False: #loop to check the time of day
        tnow = ts.now() #saves time now

        alt = sun_alt(tnow)
        if alt < 5:
            datenow = tnow.utc_strftime("%Y%m%d")
            timestr = tnow.utc_strftime("%H:%M:%S")
            path = f"out/{datenow}"
            os.mkdir(path) #makes directory for images on new night
            #log
            log = open(f"{path}/log-{datenow}.txt", "w")
            log.write(f"LOG FOR THE NIGHT OF {datenow} CREATED @ {timestr}\n")
            log.write(f"Altitude of sun: {alt} \n")

            camera.start_preview() #starts the camera
            time.sleep(2)
            log.write("Camera started\n\n")
            active = True #sets active status to True is altitude of sun is below 5 degs
        else:
            time.sleep(10) #checks every 10seconds if it is nighttime


    ## NIGHT-TIME MODE ##
    while active == True:

        ## DOME OPEN MODE ##
        while domestatus == False:
            #need the time first
            tnow = ts.now() #saves time now

            tnowstr = tnow.utc_strftime("%Y-%m-%d %H:%M:%S") #string version
            tnowfn = tnow.utc_strftime("%Y%m%d_%H%M%S") #filename version
            timestr = tnow.utc_strftime("%H:%M:%S")

            #capture image
            img_name = f"{tnowfn}_{devname}.jpg"
            camera.capture(f"{path}/{img_name}")
            log.write(f"Image {img_name} captured @ {timestr}\n")

            alt = sun_alt(tnow)
            log.write(f"Altitude of sun: {alt} \n")

            #checks if it is nighttime otherwise go to day-time mode
            if alt > 5:
                active = False #sets active status to False if altitude of sun is above 5 degs
                camera.stop_preview() #stops camera
                log.write(f"\n END OF NIGHT \n")
                log.close()
                break

            #calculate the time of day
            mode = timeoday(alt)
            log.write(f"Time of day: {mode} \n")

            #calculate moon's alt, phase, and illumination
            malt, mphase, mill = moon_props(tnow)

            #read image metadata
            with open(f"{path}/{img_name}", "rb") as photo:
                meta = Image(photo)

            ## DETECT IF DOME IS OPEN OR CLOSED ##
            domestatus = dome_detect(f"{path}/{img_name}")
            if domestatus == True:
                result = "Closed"
            else:
                result = "Open"

            log.write(f"Dome is {result} \n")


            #construct dict of these values to be turned into JSON
            values = {"device":prams["device_name"],"time":tnowstr,
            "image":{"name":img_name,"exposure time":meta["exposure_time"], "width":meta["image_width"], "height":meta["image_height"]},
            "location":{"name":prams["location"],"latitude":prams["latitude"],"longitude":prams["longitude"],"elevation":prams["elevation"]},
                      "period of the day":mode,
                      "sun":{"altitude":round(alt,7)},
                      "moon":{"altitude":round(malt,7),"phase":round(mphase,7),"illumination":round(mill,7)},
                      "dome-status": result
                     }
            #saves json
            with open(f'{path}/{img_name[:-4]}.json', 'w') as fp:
                json.dump(values, fp,indent=4)
            log.write(f"JSON file saved \n\n")


        ## DOME CLOSED MODE ##
        while domestatus == True:
            tnow = ts.now() #saves time now
            timestr = tnow.utc_strftime("%H:%M:%S")

            log.write(f"Checking dome status @ {timestr} \n")

            alt = sun_alt(tnow)
            if alt > 5:
                active = False #sets active status to False if altitude of sun is above 5 degs
                camera.stop_preview() #stops camera
                log.write(f"\n END OF NIGHT \n")
                log.close()
                break

            #when dome is close image is taken continually until it seems that dome has reopened
            img_name = ".glance.jpg" #same name so glance is always overwritten
            camera.capture(f"{path}/{img_name}")

            ## DETECT IF DOME IS OPEN OR CLOSED ##
            domestatus = dome_detect(f"{path}/{img_name}")
            log.write(f"Has the dome remained closed? {domestatus} \n\n")
