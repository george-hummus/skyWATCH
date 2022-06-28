'''
Version 0.6 of the new capture script for the skyWATCH camera - significantly re-written.
What it does:
- calculates whether it should open depending on the time of day
- if in day time mode:
    - checks every min if sun is less than 1 degrees above horizon
    - if it is then changes to night-time mode and makes directory to save images to
    - if not it stays in day-time mode
- if in night-time mode
    - takes an expsoure using subprocess to call raspistill; estimates the exposure time of the next image using a an estimate for the sensor's light senestivity and the previous exposure.
    - checks if it is still night-time mode (if not switches to day-time; if so continues).
    - calculates time of day (depends on sun's altitude)
    - calculates the moon's altitude, phase, and illumination
    - reads images metadata (exposure time, height, width, etc.,)
    - saves all info to JSON file with same name as image and in same directory
    - detects if the dome is open
        - if it is closed it sleeps for 1 min then takes a tempoary image when dome is closed to check if it has reopened
        - also automatically creates a placeholder image used in timelpase for when dome is closed
    - creates a log for the night where it notes down key info
    - at the end of the night it converts the images into a timeplase mp4
    - changes the exposure time on the fly with each new image for best all-sky image
    - need to account for dome closing when automating the exposure time
    - clears memory after each night capture to reduce the load on the raspberry pi zero
- records any errors it may ecounter in a log


To-do:
- make option to load in your own templates for the dome detect (or it could make ones for you?)
- make version for the new pi-cam api
- include the temperature sensor readings

Author: George Hume
2022
'''

## IMPORTS ##
from skyfield.api import N,E, wgs84, load
import time
from Cfunctions import *
import gc

### SETUP ###
prams = setup() #loads in setup json containing the paramters for the device and its location

#defines the name of the device
devname = prams["device_name"]

#loads in ephemerides and time scale
eph = load('de421.bsp')
ts = load.timescale()

#sets up sun and moon plus position on earth
earth, sun = eph['earth'], eph['sun']
Epos = earth + wgs84.latlon(prams["latitude"] * N, prams["longitude"] * E, elevation_m=prams["elevation"])

#defines the inital conditions
active = False #boolean to check if cam should start exposing - starts on False
domestatus = False #boolean to check if the dome is open or not - starts on False (open)
exptime = 500000 #inital exp time - starts at 0.5s (units are ns)
templims = [[[122,172],[520,570]],[[107,157],[28,78]]] #limits for the template matching
templates = ['dome-templates/hflr-template1.jpg', 'dome-templates/hflr-template2.jpg'] #paths to templates


### OPERATIONAL LOOP ###
while True:

    ## DAY TIME MODE ##
    while active == False:
        # check the time to see if sun is less than 1deg above horizon #
        tnow = ts.now() #saves time now

        active = sun_check(Epos,tnow,sun)
        if active == True:
            path,logname,imlist,datenow = startup(tnow,devname)
            break
        else:
            time.sleep(10) #checks sun's altitude every min


    ## NIGHT TIME MODE ##
    while active == True:
        # check the time to see if sun is less than 1deg above horizon #
        tnow = ts.now() #saves time now
        active = sun_check(Epos,tnow,sun)

        # convert time into stings #
        timestr = tnow.utc_strftime("%H:%M:%S")
        tnowfn = tnow.utc_strftime("%Y%m%d_%H%M%S")
        logger(logname,f"Time: {timestr}\n")

        if active == False:
            logger(logname,f"Ending captures for the night and creating timelapse.\n")
            timelapse(imlist,f'{path}/timelapse-{datenow}_{devname}.mp4')
            logger(logname,f"Timelapse movie saved as: timelapse-{datenow}_{devname}.mp4\n")

            logger(logname,"\nNIGHT END\n")
            break
        else:
            # low resolution glance #
            img_path = ".glance.jpg"
            temp_exptime = capture(img_path,exptime,res=[825,640]) #temp exp time, will be made offical if dome is open

            # check the status of the dome using glance #
            domestatus = dome_detect(img_path,templates,templims)


        # OPEN DOME MODE #
        if domestatus == False:
            # logs dome is open #
            logger(logname,"Dome is open\n")
            exptime = temp_exptime


            # call for current time again #
            tnow = ts.now()
            tnowstr = tnow.utc_strftime("%Y-%m-%d %H:%M:%S") #string version
            tnowfn = tnow.utc_strftime("%Y%m%d_%H%M%S") #filename version
            timestr = tnow.utc_strftime("%H:%M:%S")


            # capture full resolution image #
            img_name = f"{tnowfn}_{devname}.jpg"
            img_path = f"{path}/{img_name}"
            exptime = capture(img_path,exptime)
            logger(logname,f"Image {img_name} captured @ {timestr}\n") #logs capture

            imlist.append(img_path) #appends path to image to list of images
            logger(f"{path}/images.list",f"{img_path}\n") #appends path to image to file of list of images


            # collects all info #
            skyprops = SnM(Epos,tnow,eph) #solar, day period, and lunar properties
            improps = Iprops(img_path) #image properties


            # saves info as a JSON #
            im_json(img_name,timestr,skyprops,improps,prams,path)
            logger(logname,f"JSON saved as {img_name[0:-4]}.json\n")


            # add blank line to night log
            logger(logname,"\n")
            # 60 delay between captures
            time.sleep(60)


        # CLOSED DOME MODE #
        else:
            # logs dome is closed #
            logger(logname,"Dome is closed\n\n")


            # makes placeholder and appends it to image list and file #
            img_path = f"{path}/PH-{tnowfn}_{devname}.jpg"
            placeholder(devname, prams["location"], timestr, img_path)
            imlist.append(img_path) #appends path to image to list of images
            logger(f"{path}/images.list",f"{img_path}\n") #appends path to image to file of list of images

            # delay #
            time.sleep(60)

        gc.collect() #garbage collection at end of each cycle to free up memory
