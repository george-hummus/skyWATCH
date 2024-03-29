'''
Day testing version of v0.8 of the capture script for the skyWATCH camera - depends on the Cfunctions.py file.

What it does:
- starts regardless of the time of day and will loop 20 times, producing 20 images
- detects if the dome is open via taking a low-resolution temporary image
- if the dome is open:
    - takes an exposure using subprocess to call raspistill; estimates the exposure time this image using an estimate for the sensor's light sensitivity and a lower resolution temporary image taken at with the exposure time of the previous on sky image (max exposure time for pi HQ camera is set to be 90s).
        - images are annoted with device name, location, time, and exposure time
        - images are saved as greyscale due to issue with `-awb greyworld` not working in raspistill
    - calculates the time of day (depends on the sun's altitude)
    - calculates the moon's altitude, phase, and illumination
    - saves all info to a JSON file with the same name as the image and in the same directory
- if the dome is closed:
    - device sleeps for 1 min then takes a temporary image each minute to check if it has reopened
    - also automatically creates a placeholder image used in timelapse for when the dome is closed

- clears memory after each night capture to reduce the load on the raspberry pi
- all exposures can be specified to be in JPG or PNG format (via editing the setup file)
- no longer any set time delays between captures
- at the end of the night it converts the images into a timelapse mp4


* in this daytime testing script a separate timestamped testing log is printed out and all the dome detection glances are saved *


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

## Set-up device paramters ##
prams = setup() #loads in setup json containing the paramters for the device and its location
#defines the name of the device
devname = prams["device_name"]
#defines the image format to save the images as
ifmt = prams["image_format"]

## Set-up ephemerides ##
#loads in ephemerides and time scale
eph = load('de421.bsp')
ts = load.timescale()
#sets up sun and moon plus position on earth
earth, sun = eph['earth'], eph['sun']
Epos = earth + wgs84.latlon(prams["latitude"] * N, prams["longitude"] * E, elevation_m=prams["elevation"])

## Set-up for capturing ##
active = False #boolean to check if cam should start exposing - starts on False so can do start up
exptime = 500000 #inital exp time - starts at 0.5s (units are micro seconds)
fullres = [4065, 3040] #defines the full resolution of the images

## Set-up for Dome detection ##
domestatus = True #boolean to check if the dome is open or not - starts on True (closed)
templates = ['dome-templates/hflr-template1.jpg', 'dome-templates/hflr-template2.jpg'] #paths to templates
l1 = [[104,204],[75,175]] #inital xy coordinate limits for template 1
l2 = [[505,506],[6,106]] #inital xy coordinate limits for template 2
maxL = [[[25,325],[25,225]],[[450,735],[0,200]]] #max coordinate limits for template 1 and 2


### OPERATIONAL LOOP ###
while True:

    ## DAY TIME MODE ##
    while active == False:
        # check the time to see if sun is greater than 6 deg below horizon (ie., it is not daytime or civil twilight) #
        tnow = ts.now() #saves time now

        active = True
        if active == True:
            path,logname,imlist,datenow = startup(tnow,devname,pextra="-daytest") #different dir path to differentiate directory from real outputs
            logger(logname,f"Capture Script Version: 0.8-daytest \n\n")
            print("Night started @ ", dt.datetime.now().strftime("%H:%M:%S"),"\n") ##
            i = 1 #start of exposure counter
            break
        else:
            time.sleep(60) #checks sun's altitude every min


    ## NIGHT TIME MODE ##
    while active == True:
        # check the time to see if sun is greater than 6 deg below horizon (ie., it is not daytime or civil twilight) #
        tnow = ts.now() #saves time now

        if i > 20:
            active = False
        else:
            active = True

        # convert time into stings #
        timestr = tnow.utc_strftime("%H:%M:%S")
        tnowfn = tnow.utc_strftime("%Y%m%d_%H%M%S")
        logger(logname,f"Time: {timestr}\n")

        if active == False:
            logger(logname,f"Ending captures for the night and creating timelapse.\n")
            print("Night ended @ ", dt.datetime.now().strftime("%H:%M:%S")) ##
            timelapse(imlist,f'{path}/timelapse-{datenow}_{devname}.mp4')
            logger(logname,f"Timelapse movie saved as: timelapse-{datenow}_{devname}.mp4\n")
            print("Saved timelapse @ ", dt.datetime.now().strftime("%H:%M:%S")) ##

            logger(logname,"\nNIGHT END\n")
            exit() #exits after 20 loops
        else:
            print(f"Loop {i}")

            # low resolution glance for dome detection #
            glance_path = f"{path}/.glance_{tnowfn}.{ifmt}"

            print("glanced @ ", dt.datetime.now().strftime("%H:%M:%S")) ##

            temp_exptime = capture(glance_path,exptime,res=[825,640]) #temp exp time, will be made offical if dome is open

            print("finshed glancing @ ", dt.datetime.now().strftime("%H:%M:%S"),f"- with exptime of {temp_exptime/1e6}") ##


            # check the status of the dome using glance and NEW dome detection function #
            domestatus,l1,l2 = dome_detect2(glance_path, templates, l1, l2, maxL, domestatus)
            print("checked if dome is open @ ", dt.datetime.now().strftime("%H:%M:%S")) ##


        # OPEN DOME MODE #
        if domestatus == False:
            # logs dome is open #
            logger(logname,"Dome is open\n")
            exptime = temp_exptime


            # call for current time again #
            tnow = ts.now()
            tnowstr = tnow.utc_strftime("%Y-%m-%d %H:%M:%S") #string version of datetime
            tnowfn = tnow.utc_strftime("%Y%m%d_%H%M%S") #filename version
            timestr = tnow.utc_strftime("%H:%M:%S") #string version of time

            print("Dome is open @ ", dt.datetime.now().strftime("%H:%M:%S")) ##

            # capture full resolution image #
            img_name = f"{tnowfn}_{devname}.{ifmt}"
            img_path = f"{path}/{img_name}"
            print("start full res capture @ ", dt.datetime.now().strftime("%H:%M:%S")) ##
            st = time.time() #start time
            exptime = capture(img_path,exptime,res=fullres,ann=True,prams=prams,t=tnowstr)
            et = time.time() #end time
            print("captured full res image @ ", dt.datetime.now().strftime("%H:%M:%S"),f"- with exptime of {exptime/1e6}s this took {et-st} seconds") ##
            logger(logname,f"Image {img_name} captured @ {timestr}\n") #logs capture

            imlist.append(img_path) #appends path to image to list of images
            logger(f"{path}/images.list",f"{img_path}\n") #appends path to image to file of list of images


            # collects all info #
            skyprops = SnM(Epos,tnow,eph) #solar, day period, and lunar properties
            improps = [exptime/1e6, fullres[0], fullres[1]] #saves exptime (in secs), and image width and height


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
            print("dome is closed @ ", dt.datetime.now().strftime("%H:%M:%S")) ##

            # makes placeholder and appends it to image list and file #
            ph_path = f"{path}/PH-{tnowfn}_{devname}.{ifmt}"
            placeholder(devname, prams["location"], timestr, ph_path, glance_path)
            print("made placeholder @ ", dt.datetime.now().strftime("%H:%M:%S")) ##
            imlist.append(img_path) #appends path to image to list of images
            logger(f"{path}/images.list",f"{img_path}\n") #appends path to image to file of list of images

            # delay of 60s if dome is closed #
            time.sleep(60)
            print("finished 60s of sleep @ ", dt.datetime.now().strftime("%H:%M:%S")) ##

        print("start memory clean up @ ", dt.datetime.now().strftime("%H:%M:%S")) ##
        gc.collect() #garbage collection at end of each cycle to free up memory
        print("end memory clean up @ ", dt.datetime.now().strftime("%H:%M:%S")) ##
        print("\n") ##

        i+=1
