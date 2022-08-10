'''
Functions used within the capture scripts from v0.5 upwards.

Author: George Hume
2022
'''
### IMPORTS ###
from skyfield import almanac
import json
import glob
import cv2 as cv
import numpy as np
from exif import Image
import os
import subprocess

##############################################################################################################

def setup():
    ### Loads in the parameters from the JSON setup file, or gets you to create one if it does not exsist

    if len(glob.glob("setup.json")) == 0: #if no setup file then you'll be prompted to create one
        print("Welcome to first time setup of skyWATCH camera!")
        devname = input("Name of device: ")
        locname = input("Name of the location: ")
        lat = input("Latitude of location (in decimal degrees): ")
        long = input("Longitude of location (in decimal degrees): ")
        elv = input("Elevation above sea-level of location (in meteres): ")
        prams = {"device_name":devname,"location":locname,"latitude":float(lat),"longitude":float(long),"elevation":float(elv)} #saves parameters as a directory, which will be used in the capture scipt and to save the JSON
        with open('setup.json', 'w') as fp: #saves setupfile as a json
            json.dump(prams, fp,indent=4)

    else: #otherwise it reads the setup file
        with open('setup.json', 'r') as f:
            prams = json.load(f)

    return prams

##############################################################################################################

def logger(logname,string):
    ### appends lines to a text file

    with open(logname, 'a') as f:
        f.write(string)

##############################################################################################################

def testlog(path,list):
    ### appends all elements of a list to a line in a text file

    with open(f"{path}/testlog.txt", 'a') as f:
        for element in list:
            f.write(str(element))

##############################################################################################################

def sun_check(Epos,t,sun):
    ### Finds the altitude of the sun, for the given location and time of day
    ## Sets active varible, depending on altitude of the sun
    # Epos is location of device; t is the time; sun is the sun ephemerides file

    astro = Epos.at(t).observe(sun)
    app = astro.apparent()
    alt, az, distance = app.altaz()

    salt = alt.degrees

    if salt > -6.0: #only starts night mode when in nautical twilight or darker
        return False
    else:
        return True

##############################################################################################################

def startup(t,devname):
    ### Start up function for when switch to night mode
    ## Creates new directory to save images to, creates the log and the image list
    # t is the current time

    # strings for current date and time
    datenow = t.utc_strftime("%Y%m%d")
    timestr = t.utc_strftime("%H:%M:%S")

    # creates the directory for the night
    path = f"out/{datenow}"
    os.mkdir(path)

    #creates the night log
    logname = f"{path}/log-{datenow}_{devname}.log"
    logger(logname,f"LOG FOR THE NIGHT OF {datenow[6:]}/{datenow[4:6]}/{datenow[0:4]} CREATED @ {timestr}\n")

    img_list = [] #creates a list of the images captured during the night, used to construct the timeplase

    return path,logname,img_list,datenow

##############################################################################################################

def dome_detect(fname,templates,xy):
    ### DETECTS IF DOME IS OPEN OR CLOSED
    ## fname is the name of captured image; templates is list of the templates used to detect if the dome is closed; xy is a list containing the x detection limits at index 0 and y detection limits at index 1; res is size you want to shink images too when processing, default is full res

    # uses openCV to read image
    img = cv.imread(fname,0)

    # post processing of image to highlight dome fetures
    img = np.invert(cv.equalizeHist(img)).clip(min=150)

    method = eval('cv.TM_CCOEFF') #define method to match tmeplates to image

    results = [] #empty list to append matching results to

    #split the x and y limits
    limsx = xy[0]
    limsy = xy[1]

    for j in range(len(templates)): # matches however many templates there are

        template = cv.imread(templates[j],0) #loads template

        # Apply template Matching
        res = cv.matchTemplate(img,template,method)
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)

        #checks if predicted location of template in image is within the x and y limits of the true position (if not then its likely the dome is open)
        if (max_loc[0] > limsx[j][0]) & (max_loc[0] < limsx[j][1]):
            if (max_loc[1] > limsy[j][0]) & (max_loc[1] < limsy[j][1]):
                results.append(True)
            else:
                results.append(False)
        else:
            results.append(False)

    domestatus = (results[0] or results[1])

    return domestatus

##############################################################################################################

def capture(fname,etime,res=[4065, 3040],ann=False):
    ### captures an image using subprocess to use the raspistill command, and estimates the neccessary exposure time needed before with a lower resolution glance
    ## fname is the path to where the final image will be saved, etime is the exposure time for the glance - from this the neccessary exposure time will be estimated, res is the resolution needed for the final image, ann is boolean if you want the image to be annotated


    #function to use subprocess to capture image with raspistill
    def command(width,height,et,imname,a):
        if a==False:
            cmd = f"raspistill -w {width} -h {height} -t 10 -bm -ss {et} -o {imname} -ag 6 -awb greyworld -e png"
        else:
            cmd = f"raspistill -w {width} -h {height} -t 10 -bm -ss {et} -o {imname} -ag 6 -awb greyworld -e png -ae 64,0xff,0x808000 -a 1024 -a ' Image: {fname[13:]} | Expsoure time: {float('%.2g' % (et/10e6))} s '"
        return cmd


    # low res glance used to estimate exp time needed #
    width, height = 825, 640
    imname = ".glance.png"
    cmd = command(width,height,etime,imname,a=False)
    subprocess.call(cmd,shell=True)


    # estimate neccessary expsoure time #
    flat = cv.imread(".glance.png",0).flatten() #read in glance as 1d array of pixel values
    median = np.median(flat) #median of the pixel counts of the glance
    if median == 0:
        median = 1 #to avoid divide by zero errors

    #upper and lower bound the median should be within
    LB = 96
    UB = 160
    if (median>LB) & (median<UB):
        exptime=etime #if within bounds captures image at same exp-time
    else: #if median is not within this range
        diff = (128/(median))**1.6 #assumes x^1.6 response curve of camera sensor
        exptime = etime*diff
        if exptime > 90000000: #max exptime set to 90s
            exptime = 90000000
        else:
            exptime=exptime


    # captures the final image #
    width, height = res[0], res[1] #back to desired image size
    cmd = command(width,height,exptime,fname,a=ann)
    subprocess.call(cmd,shell=True) #take highres image


    # returns the calculated expsoure time so it can be used in the next capture #
    return exptime

##############################################################################################################

def newcapture(fname,etime,res=[4065, 3040]): ## INPROGRESS ##
    ### captures an image using subprocess to use the libcamera-still command for pi with Bullseye OS, and estimates the neccessary exposure time needed before with a lower resolution glance
    ## fname is the path to where the final image will be saved, etime is the exposure time for the glance - from this the neccessary exposure time will be estimated, res is the resolution needed for the final image

    """
    #function to use subprocess to capture image with raspistill
    def command(width,height,et,imname):
        cmd = f"raspistill -w {width} -h {height} -t 10 -bm -ex off -ag 1 -ss {et} -ag 6 -o {imname}"
        return cmd


    # low res glance used to estimate exp time needed #
    width, height = 825, 640
    imname = ".glance.jpg"
    cmd = command(width,height,etime,imname)
    subprocess.call(cmd,shell=True)


    # estimate neccessary expsoure time #
    flat = cv.imread(".glance.jpg",0).flatten() #read in glance as 1d array of pixel values
    median = np.median(flat) #median of the pixel counts of the glance
    if median == 0:
        median = 1 #to avoid divide by zero errors

    #upper and lower bound the median should be within
    LB = 96
    UB = 160
    if (median>LB) & (median<UB):
        exptime=etime #if within bounds captures image at same exp-time
    else: #if median is not within this range
        diff = (128/(median))**1.6 #assumes x^1.6 response curve of camera sensor
        exptime = etime*diff
        if exptime > 230000000: #max exptime of pi hq camera is 230s
            exptime = 230000000
        else:
            exptime=exptime


    # captures the final image #
    width, height = res[0], res[1] #back to desired image size
    cmd = command(width,height,exptime,fname)
    subprocess.call(cmd,shell=True) #take highres image
    """


    exptime = 0
    # returns the calculated expsoure time so it can be used in the next capture #
    return exptime

##############################################################################################################

def captest(fname,etime):
    ### Capture function for testing mode; so doesn't use raspistill to capture images
    ## fname is the path to where the test image, etime is the exposure time for the glance - from this the neccessary exposure time will be estimated.

    # estimate neccessary expsoure time #
    flat = cv.imread(fname,0).flatten() #read in glance as 1d array of pixel values
    median = np.median(flat) #median of the pixel counts of the glance

    #upper and lower bound the median should be within
    LB = 96
    UB = 160
    if (median>LB) & (median<UB):
        exptime=etime #if within bounds captures image at same exp-time
    else: #if median is not within this range
        diff = (128/median)**1.6 #assumes x^1.6 response curve of camera sensor
        exptime = etime*diff
        if exptime > 230000000: #max exptime of pi hq camera is 230s
            exptime = 230000000
        else:
            exptime=exptime

    return exptime


##############################################################################################################

def SnM(Epos,t,eph):
    ### Finds the alitude of the sun, moon's alt, phase, and illumination, and the time of day
    ## Epos is location of device; t is the time; eph is the ephemerides file

    sun, moon = eph['sun'],eph['moon']

    # finds the altitude of the sun #
    astro = Epos.at(t).observe(sun)
    app = astro.apparent()
    alt, az, distance = app.altaz()
    alt = alt.degrees


    # infers time of day from alitude of the sun #
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


    #calculate moon's alt, phase, and illumination
    mastro = Epos.at(t).observe(moon)
    mapp = mastro.apparent()
    malt, maz, mdst = mapp.altaz()
    mphase = almanac.moon_phase(eph, t)
    mill = almanac.fraction_illuminated(eph,"moon",t)


    # returns all the varibles as a list
    return [alt, mode , [malt.degrees,mphase.degrees,mill]]

##############################################################################################################

def Iprops(fname):
    ### Finds the exposure time, width and height of the captured image
    ## fname is the path to the image
    with open(fname, "rb") as photo:
        meta = Image(photo)

    # returns list with the exposure time, width, and height of the captured image
    return [meta["exposure_time"], meta["image_width"], meta["image_height"]]

##############################################################################################################

def im_json(fname,t,skyprops,iprops,devprops,path):
    ### writes the JSON collecting all the properties of the captured image
    ## fname is the name of the image; t is the time as a string; skyprops is a list containing alitude of the sun, moon's alt, phase, and illumination, and the time of day; iprops is a list containing the exposure time, width and height of the captured image; devprops is a dictonary containing the name of the device and its location; path is the path to the directory the JSON will be saved to


    # constructs a dict of these values to be turned into JSON #
    values = {"device":devprops["device_name"],"time":t,
    "image":{"name":fname,"exposure time":iprops[0], "width":iprops[1], "height":iprops[2]},
    "location":{"name":devprops["location"],"latitude":devprops["latitude"],"longitude":devprops["longitude"],"elevation":devprops["elevation"]},
              "period of the day":skyprops[1],
              "sun":{"altitude":round(skyprops[0],7)},
              "moon":{"altitude":round(skyprops[2][0],7),"phase":round(skyprops[2][1],7),
              "illumination":round(skyprops[2][2],7)}
             }


    # saves the dictonary as a JSON #
    with open(f'{path}/{fname[:-4]}.json', 'w') as fp:
        json.dump(values, fp,indent=4)

##############################################################################################################

def timelapse(images,path,res=[825,640]):
    ### makes timeplase from images taken during the night
    ## images is a list of paths to the images saved during the night (in chronological order), path is the path to which the timelapse will be saved to, res is the resolution of the final video (default is 480p 4:3)

    img_array=[] #empty list to save with image arrays

    for fname in images:
        if len(glob.glob(fname)) != 0: #makes sure the image is present in the directory
            img = cv.imread(fname)
            img = cv.resize(img, res)#resize to 480p with same aspect ratio so pi-zero can cope
            height, width, layers = img.shape
            size = (width,height)
            img_array.append(img)

    out = cv.VideoWriter(path, cv.VideoWriter_fourcc(*'mp4v'), 5, size)

    for im in img_array:
        out.write(im)

    out.release() #saves the timelapse

    img_array=[] #clears the image array from memory

##############################################################################################################

# function to construct the whole thing
def placeholder(dev, loc, t, opath, glance):
    ''' Produces an automated placeholder image for given:
    - device name (less than 16 charcaters) - dev
    - location name (less than 16 charcaters) - loc
    - UTC time (in format HH:MM:SS) - t
    Overlays the placeholder onto the glance image that indicated the
    dome was close located at path `glance`.
    Saves to path and file name given by `opath` argument.
        Note, only accepts alphanumeric characters and colons,
        any other charcters will be replaced with unknown charcter symbol.
    '''

    #loads in dict with the arrays corresponding to the letters
    letsnums=np.load("chars.npy",allow_pickle=True).item()
    #spacing tiles
    blanktile = np.zeros([20,10])
    halfblank = np.zeros([20,5])


    #placeholder image is 240x180 split into 24 columns and 9 rows

    #cuts down the names if they are too long
    dev=dev[0:16]
    loc=loc[0:14]

    #text for each line of the image lines 0,1,7 & 8 are blank lines
    line2str = "skywatch"
    line3str = "dome is closed"
    line4str = f"time: {t} utc"
    line5str = f"device: {dev.lower()}" #makes lower case to match dict keys
    line6str = f"location: {loc.lower()}"

    #making the blank lines for lines 0,1,7 & 8
    emptyline = []
    for i in range(24):
        emptyline.append(blanktile)
    emptyline = np.concatenate(emptyline,axis=1)

    def makeline(string):
        #function that makes a string into a line in the image whihc is centred

        # uses dict of letters corresponding to arrays representing them 2 make the line
        phrase = [] #empty line
        for j in string:
            if j == " ":
                phrase.append(blanktile) #insert blank tile if there is space in string
            else:
                try: #looks for corresponding array for the character
                    phrase.append(letsnums[j])
                except: #if can't find charcater in dict replaces it with unknown char
                    phrase.append(letsnums["unknown"])

        phrase = np.concatenate(phrase,axis=1) #concatenates the line into a 2d array

        spacing=(24-len(string))/2
        #calculates spacing needed at each side for centred string in image

        if spacing > 0: #if zero the max length is reached
            if (spacing%1 != 0):
                space = [halfblank]
                #if odd number of space left need half tiles needed to centre string
            else:
                space = []

            for i in range(int(spacing)):
                space.append(blanktile)#appends blank tile for the number of spacing
            space = np.concatenate(space,axis=1)#convert to long 2d array

            line = np.concatenate((space,phrase,space),axis=1) #adds the spacing to str

        else:
            line = phrase #if no spacing then dont need to add any

        return line

    #uses above function to convert strings to line in images
    line2 = makeline(line2str)
    line3 = makeline(line3str)
    line4 = makeline(line4str)
    line5 = makeline(line5str)
    line6 = makeline(line6str)

    imagelist = [emptyline,emptyline,
                 line2,line3,line4,line5
                 ,line6,emptyline,emptyline] #images as list line by line

    placeholder = np.concatenate(imagelist,axis=0) #image as whole array

    # combines the placeholder with the glance image #
    cv.imwrite(".ph.png",placeholder) #save temp ph image
    g = cv.imread(glance) #load in glance
    ph = cv.imread(".ph.png") #load in temp ph image

    #invert placholder colour so can see when overlaied
    ph_inv = np.invert(ph)

    #resize placeholder to be same size as glance
    height = g.shape[0]
    width = g.shape[1]
    ph_big = cv.resize(ph_inv, [width,height])
    ph_blend = cv.addWeighted(g,0.5,ph_big,0.4,0) #blend the two images

    cv.imwrite(opath,ph_blend) #save image

##############################################################################################################
