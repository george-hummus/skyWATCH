'''
Testing version of v0.7.1 of the capture script for the skyWATCH camera - depends on the Cfunctions.py file.

What it does:
- calculates whether it should open depending on the time of day
- if in daytime mode:
    - checks every minute if the sun is less than -6 degrees above horizon (end of civil twilight)
    - if it is then changes to night-time mode, makes a directory to save images to and creates a log for the night where it notes down key info
    - if not it stays in daytime mode
- if in night-time mode
    - checks if it is still night-time mode (if not switches to day-time; if so continues).
    - detects if the dome is open via taking a low-resolution temporary image
    - if the dome is open:
        - takes an exposure using subprocess to call raspistill; estimates the exposure time this image using an estimate for the sensor's light sensitivity and a lower resolution temporary image taken at with the exposure time of the previous on sky image (max exposure time for pi HQ camera is 230s).
        - calculates the time of day (depends on the sun's altitude)
        - calculates the moon's altitude, phase, and illumination
        - reads images metadata (exposure time, height, width, etc.,)

        - saves all info to a JSON file with the same name as the image and in the same directory
    - if the dome is closed:
        - device sleeps for 1 min then takes a temporary image each minute to check if it has reopened
        - also automatically creates a placeholder image used in timelapse for when the dome is closed
        - uses separate exposure time for if the dome was previosuly closed to avoid under or over exposing the dome when if closes

    - clears memory after each night capture to reduce the load on the raspberry pi
    - no longer any set time delays between captures
    - at the end of the night it converts the images into a timelapse mp4
    - all exposures are now PNG format and are annoted with file name and exposure time (more varibles to come...)


To-do:
- make an option to load in your own templates for the dome detect (or it could make ones for you?)
- make a version for the new pi-cam api
- include the temperature sensor readings

Author: George Hume
2022
'''

## IMPORTS ##
from skyfield.api import N,E, wgs84, load
import time
from Cfunctions import *
import gc
import datetime as dt

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
fullres = [4065, 3040] #defines the full resolution of the images


### OPERATIONAL LOOP ###
while True:

    ## DAY TIME MODE ##
    while active == False:
        # check the time to see if sun is less than 1deg above horizon #
        tnow = ts.now() #saves time now

        active = sun_check(Epos,tnow,sun)
        if active == True:
            path,logname,imlist,datenow = startup(tnow,devname)
            logger(logname,f"Capture Script Version: 0.7.1 testing \n\n")
            testlog(path,["Night started @ ", dt.datetime.now().strftime("%H:%M:%S"),"\n\n"]) ##
            break
        else:
            time.sleep(60) #checks sun's altitude every min


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
            testlog(path,["Night ended @ ", dt.datetime.now().strftime("%H:%M:%S"),"\n"]) ##
            timelapse(imlist,f'{path}/timelapse-{datenow}_{devname}.mp4')
            logger(logname,f"Timelapse movie saved as: timelapse-{datenow}_{devname}.mp4\n")
            testlog(path,["Saved timelapse @ ", dt.datetime.now().strftime("%H:%M:%S"),"\n"]) ##

            logger(logname,"\nNIGHT END\n")
            break
        else:
            # low resolution glance #
            img_path = f"{path}/.glance.png"

            testlog(path,["glanced @ ", dt.datetime.now().strftime("%H:%M:%S"),"\n"]) ##

            temp_exptime = capture(img_path,exptime,res=[825,640]) #temp exp time, will be made offical if dome is open


            testlog(path,["finshed glancing @ ", dt.datetime.now().strftime("%H:%M:%S"),"\n"]) ##

            # check the status of the dome using glance #
            domestatus = dome_detect(img_path,templates,templims)
            testlog(path,["checked if dome is open @ ", dt.datetime.now().strftime("%H:%M:%S"),"\n"]) ##


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

            testlog(path,["Dome is open @ ", dt.datetime.now().strftime("%H:%M:%S"),"\n"]) ##

            # capture full resolution image #
            img_name = f"{tnowfn}_{devname}.png"
            img_path = f"{path}/{img_name}"
            testlog(path,["start full res capture @ ", dt.datetime.now().strftime("%H:%M:%S"),"\n"]) ##
            exptime = capture(img_path,exptime,res=fullres,ann=True)
            testlog(path,["captured full res image @ ", dt.datetime.now().strftime("%H:%M:%S"),"\n"]) ##
            logger(logname,f"Image {img_name} captured @ {timestr}\n") #logs capture

            imlist.append(img_path) #appends path to image to list of images
            logger(f"{path}/images.list",f"{img_path}\n") #appends path to image to file of list of images


            # collects all info #
            skyprops = SnM(Epos,tnow,eph) #solar, day period, and lunar properties
            improps = [exptime/10e6, fullres[0], fullres[1]] #saves exptime (in secs), and image width and height


            # saves info as a JSON #
            im_json(img_name,timestr,skyprops,improps,prams,path)
            logger(logname,f"JSON saved as {img_name[0:-4]}.json\n")


            # add blank line to night log
            logger(logname,"\n")
            # no delay between captures


        # CLOSED DOME MODE #
        else:
            # logs dome is closed #
            logger(logname,"Dome is closed\n\n")
            testlog(path,["dome is closed @ ", dt.datetime.now().strftime("%H:%M:%S"),"\n"]) ##

            # makes placeholder and appends it to image list and file #
            img_path = f"{path}/PH-{tnowfn}_{devname}.png"
            placeholder(devname, prams["location"], timestr, img_path, f"{path}/.glance.png")
            testlog(path,["made placeholder @ ", dt.datetime.now().strftime("%H:%M:%S"),"\n"]) ##
            imlist.append(img_path) #appends path to image to list of images
            logger(f"{path}/images.list",f"{img_path}\n") #appends path to image to file of list of images

            # delay of 60s if dome is closed #
            time.sleep(60)
            testlog(path,["finished 60s of sleep @ ", dt.datetime.now().strftime("%H:%M:%S"),"\n"]) ##

        testlog(path,["start memory clean up @ ", dt.datetime.now().strftime("%H:%M:%S"),"\n"]) ##
        gc.collect() #garbage collection at end of each cycle to free up memory
        testlog(path,["end memory clean up @ ", dt.datetime.now().strftime("%H:%M:%S"),"\n"]) ##
        testlog(path,["\n"]) ##
