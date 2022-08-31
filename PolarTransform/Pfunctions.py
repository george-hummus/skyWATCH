"""
Pfunctions: this contains the functions for use in:
 - fitting.py
 - test.py

Author: George Hume
2022
"""

import numpy as np
import matplotlib.pyplot as plt
import skyfield.api as api
from skyfield.api import N,S,E,W, wgs84,load,Star,utc
import datetime as dt
import scipy.optimize as opt

################################################################################

def pixels2polars(x,y):
    "Converts x and y pixels image coordinates with origin at top left of the image to polar coordinates (r, theta) with origin at the centre on the image. Returns r with units of pixels and theta with units of degrees."

    #middle of the image needs to be (0,0) position so need to offest the coordinates
    x1 = x - 2028
    y1 = 1520 - y
    # (2028,1520) is the centre of the image above

    # r in polars is sqrt(x^2+y^2)
    r = np.sqrt(x1**2+y1**2)

    thetas = []
    for i in range(len(x1)):
        X,Y = x1[i],y1[i]
        theta = np.arctan(Y/X)*(180/np.pi) #in degrees

        #make sure no negatives values
        if (X>0)&(Y>0): #1st quadrant
            theta = theta
        elif (X<0)&(Y>0): #2nd quadrant
            theta = 180+theta
        elif (X<0)&(Y<0): #3rd quadrant
            theta = 180+theta
        else: #4th quadrant
            theta = 360+theta

        thetas.append(theta)

    return r, np.array(thetas)

################################################################################

def radec2azalt(ra,dec,times,lat,long,elv):
    #converts the ra and dec to the az and alt of the target from a given lat, long, elevation
    #and time & date, using the skyfield library

    altitude, azimuth = [],[] #empty lists for alt and az

    for i in range(ra.shape[0]):
        #loops through each stars RA, dec and time

        star =  Star(ra_hours=(ra[i][0], ra[i][1], ra[i][2]),
                   dec_degrees=(dec[i][0], dec[i][1], dec[i][2]))
        #creates star oject from ra and dec

        eph = load('de421.bsp')
        ts = load.timescale()
        earth= eph['earth']
        Epos = earth + wgs84.latlon(lat * N, long * E, elevation_m=elv)
        #loads position

        try:
            #creates datetime object for the time the star was observed
            time = dt.datetime(int(times[i][0:4]), int(times[i][5:7]), int(times[i][8:10]),int(times[i][11:13]),int(times[i][14:16]),int(times[i][17:]),tzinfo=utc)
        except:
            print(f"Bad format of time and date on entry {i} of the CSV file. Please correct this and then try again.")
            exit()

        astro = Epos.at(ts.utc(time)).observe(star)
        app = astro.apparent()
        #observers star at time from position

        alt, az, distance = app.altaz()
        #gets the altitude and azimuth

        altitude.append(alt.degrees)
        azimuth.append(az.degrees)
        #convert into decimal degrees and append to lists

    return np.array(altitude), np.array(azimuth) #return alt and az as np arrays

################################################################################

def pa2az(theta):
    #converts the polar angle, theta to the same reference frame as the azimuth as for theta 0 degrees is in WEST and for azimuth zero degrees is at NORTH
    newpa = []

    for i in theta:
        if i >= 90:
            npa = i-90
        else:
            npa = i+270
        newpa.append(npa)

    return np.array(newpa)

################################################################################

def polar_angle(tht):
    #function to convert tht back to frame of polar angle
    PAs = []
    for i in tht:
        if i <= 270:
            theta = i+90
        else:
            theta = i-270

        PAs.append(theta)

    return np.array(PAs)

################################################################################

def rt2pcoords(r,theta):
    ##function to convert r and theta to pixels coords on image
    #convert to cartesians with origin at image centre
    x=r*np.cos(theta*(np.pi/180))
    y=r*np.sin(theta*(np.pi/180)) #need to convert theta to radians

    #convert cartesians to have origin at top left
    x0 = x+2028
    y0 = 1520-y

    return x0,y0

################################################################################

def linear(x,a,b,c,d):
    #linear function
    return a + (b*x)

################################################################################

def quadratic(x,a,b,c,d):
    #quadratic function
    return a + (b*x) + (c*(x**2))

################################################################################

def cubic(x,a,b,c,d):
    #cubic function
    return a + (b*x) + (c*(x**2)) + (d*(x**3))

################################################################################

def cosine(x,a,b,c,d):
    #cubic function
    return a*np.cos(b*x*(np.pi/180))+c

################################################################################

def fitfunc(X,z,C,name):

    if name == "linear":
        return opt.curve_fit(linear,X,z,p0=C)
    elif name == "quadratic":
        return opt.curve_fit(quadratic,X,z,p0=C)
    elif name == "cubic":
        return opt.curve_fit(cubic,X,z,p0=C)
    elif name == "cosine":
        return opt.curve_fit(cosine,X,z,p0=C)

################################################################################
