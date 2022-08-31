'''
Given a list of stars with a given x and y pixel position on any number of reference images, this script will find a best function to map the stars' RA and declination to these x and y positions. The parameters of this function will then be saved out so it can be used to locate the position of stars, given their RA and declination, on images taken with the same device.

The list of stars should be a CSV file with the columns from left to right being: source's name/identifier, the x pixel position in the reference image, the y pixel position in the reference image, the hours of RA of the source, the minutes of RA of the source, the seconds of RA of the source, the degrees of declination of the source, the arcmintues of declination of the source, the arseconds of declination of the source, the UTC time and date (format yyyy/mm/dd hh:mm:ss) of the reference image the source is in.

You can specify the kind of functions used to fit the radial distance, r, of the source from the centre of the image to altitude, a, of the source (calculated from the RA and Dec for the location and time). The options are:
- linear: r = A + Ba
- quadratic: r = A + Ba + Ca^2
- cubic: r = A + Ba + Ca^2 + Da^3
- cosine: r = Acos(Ba)+C

    You can also specifiy if you want the above coefficents to depend on the polar angle, ϑ. I.e., r also depends on the azimuth of the source. The options for these functions that map ϑ to the coeffients are the same as for r, plus constant (i.e., no dependency). The functions will be the same for all coeffients.

The coeffients for all these all these fits will be outputted as a JSON file.

Author: George Hume
2022
'''

import numpy as np
import matplotlib.pyplot as plt
import skyfield.api as api
from skyfield.api import N,S,E,W, wgs84,load,Star,utc
import datetime as dt
import scipy.optimize as opt
import argparse
from Pfunctions import *
import json

#command line arguments
parser = argparse.ArgumentParser(description = """
Given a list of stars with a given x and y pixel position on any number of reference images, this script will find a best function to map the stars' RA and declination to the x and y positions. The parameters of this function will then be saved out so it can be used to locate the position of stars, given their RA and declination, on images taken with the same device.
""")
#adding arguments to praser object
parser.add_argument('sources_path' , type = str, help = 'Path to the CSV file containing the sources.')
parser.add_argument('lat' , type = float, help = 'Lattitude of the all-sky camera location.')
parser.add_argument('long' , type = float, help = 'Longitude of the all-sky camera location.')
parser.add_argument('elv' , type = float, help = 'Elevation above sea-level of the all-sky camera location.')
parser.add_argument('rfunc' , type = str, help = 'Function to fit alt to r. Options are: linear, quadratic, cubic, cosine, or power.')
parser.add_argument('cfunc' , type = str, help = 'Function to fit the coefficents of r fucntion and the polar angle. Options are: constant, linear, quadratic, cubic, cosine, or power.')
parser.add_argument('--show' , type = bool, help = 'If set to true this will display some graphs related to the fitting.', default = False)
args = parser.parse_args()

## checking functions asked for are valid
rcheck = ["linear", "quadratic", "cubic", "cosine"]
ccheck = ["constant","linear", "quadratic", "cubic", "cosine"]
if args.rfunc not in rcheck:
    print(f"Invalid value of rfunc, options are {rcheck}, please try again.")
    exit()
if args.cfunc not in ccheck:
    print(f"Invalid value of cfunc, options are {ccheck}, please try again.")
    exit()

## dict of possible rfunc functions
fdict = {"linear":linear, "quadratic":quadratic, "cubic":cubic, "cosine":cosine}


## unpacking the CSV file
try:
    pos = np.loadtxt(args.sources_path,delimiter=",",usecols = (1,2),skiprows=1)
    names = np.loadtxt(args.sources_path,delimiter=",",usecols = 0,skiprows=1,dtype=str)
    RA = np.loadtxt(args.sources_path,delimiter=",",usecols = (3,4,5),skiprows=1)
    DEC = np.loadtxt(args.sources_path,delimiter=",",usecols = (6,7,8),skiprows=1)
    times = np.loadtxt(args.sources_path,delimiter=",",usecols = 9,skiprows=1,dtype=str)
except:
    print("Something went wrong unpacking the CSV file of targets. Please check the path is correct and the columns in the file are correct and try again.")
    exit()

## seperate position into x and y coords
x,y = pos.T[0], pos.T[1]

## convert to polars
r, theta = pixels2polars(x,y)

## convert RA and DEC to ALT and AZ
ALT, AZ = radec2azalt(RA,DEC,times,args.lat,args.long,args.elv)


## Fitting the azimuth to the polar angle ##
tht = pa2az(theta) #convert theta to same reference frame as azimuth

# fit to staight line
AT_results = opt.curve_fit(linear,AZ,tht,p0=[0,1,0,0])
ATa, ATb, ATc, ATd = AT_results[0][0], AT_results[0][1],0,0 #coefficents of the fit


## Fitting alitude to the radial distance ##

#dictonary of guess paramters for each function
p0s = {"linear":[-22.5,2028,0.0001,0.0001],
"quadratic":[2028,0,0.25,0.0001],
"cubic":[2028,0.0001,0.0001,0.0028],
"cosine":[2028,1,0.0001,0.0001]}

if args.cfunc=="constant":

    AR_results = fitfunc(ALT,r,p0s[args.rfunc],args.rfunc)

else:
    #define new function where the coefficents vary with theta
    def newfunc(X,a1,a2,a3,a4,b1,b2,b3,b4,c1,c2,c3,c4,d1,d2,d3,d4):
        alt, theta = X

        #assuming the coefficents are related to theta by cosine function
        A = fdict[args.cfunc](theta,a1,a2,a3,a4)
        B = fdict[args.cfunc](theta,b1,b2,b3,b4)
        C = fdict[args.cfunc](theta,c1,c2,c3,c4)
        D = fdict[args.cfunc](theta,d1,d2,d3,d4)

        R = fdict[args.rfunc](alt,A,B,C,D)

        return R

    #fit new function

    A , B, C, D = p0s[args.rfunc]

    #dictonary of guess paramters for each coefficent function split up consituent parts
    p1s = {"linear":[[A,0.1,0,0],
    [B,0.1,0,0],
    [C,0.1,0,0],
    [D,0.1,0,0]
    ],
    "quadratic":[[A,0,0.1/(A**2),0],
    [B,0,0.1/(B**2),0],
    [C,0,0.1/(C**2),0],
    [D,0,0.1/(D**2),0]
    ],
    "cubic":[[A,0,0,0.1/(A**3)],
    [B,0,0,0.1/(B**3)],
    [C,0,0,0.1/(C**3)],
    [D,0,0,0.1/(D**3)]
    ],
    "cosine":[[0.1,1,A,0],
    [0.1,1,B,0],
    [0.1,1,C,0],
    [0.1,1,D,0]
    ]}

    AR_results = opt.curve_fit(newfunc,[ALT,theta],r,p0=p1s[args.cfunc])


## Saving to JSON ##
jsondict = {"theta-az fit":{"function":"linear","fitted coeffients":[ATa, ATb, ATc, ATd]},"r-alt fit":{"function":args.rfunc,"fitted coeffients":list(AR_results[0])},"device info":{"lat":args.lat,"long":args.long,"elv":args.elv}}
with open(f'out-{args.rfunc}-{args.cfunc}.json', 'w') as fp: #saves setupfile as a json
    json.dump(jsondict, fp,indent=4)


## Plotting the fits (if show is true) ##
if args.show == True:
    fig, ax = plt.subplots(1,2,figsize=(20,10))

    #az and theta plot
    ax[0].scatter(AZ,tht)
    az = np.arange(0,360,1)
    ax[0].plot(az,linear(az,ATa, ATb,0,0),c="orange",label=r"$\theta'=$"+f"{round(ATa,3)}+{round(ATb,3)}$a_z$")
    ax[0].set_xlabel("azimuth, $a_z$ ($^o$)")
    ax[0].set_ylabel(r"adjusted polar angle, $\theta'$ ($^o$)")
    ax[0].set_xlim([0,360])
    ax[0].set_ylim([0,360])

    #alt and r plot
    ax[1].scatter(ALT,r,c=AZ)
    alt = np.arange(0,90,1)
    if args.cfunc=="constant":
        fittedline = fdict[args.rfunc](alt,AR_results[0][0],AR_results[0][1],AR_results[0][2],AR_results[0][3])
        label = "best fit line"
    else:
        fittedline = newfunc([alt,90],AR_results[0][0],AR_results[0][1],AR_results[0][2],AR_results[0][3],
        AR_results[0][4],AR_results[0][5],AR_results[0][6],AR_results[0][7],
        AR_results[0][8],AR_results[0][9],AR_results[0][10],AR_results[0][11],
        AR_results[0][12],AR_results[0][13],AR_results[0][14],AR_results[0][15])
        label = r"best fit line with constant $\vartheta$ ($=180^o$)"
    ax[1].plot(alt,fittedline,"--m",label=label)
    ax[1].set_xlabel("altitude, $a_{lt}$ ($^o$)")
    ax[1].set_ylabel(r"radial distance, $r$ ($^o$)")
    ax[1].set_xlim([0,90])
    ax[1].set_ylim([0,max(fittedline)])

    ax[0].legend()
    ax[1].legend()
    plt.show()

    # countour lines of constant altitude
    altitudes = np.arange(0,100,10) #range of alitudes from zero to 90 degrees in steps of 10

    PAs = np.arange(0,360,1) #all values of theta (0->360 degrees) in steps of 1

    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'},figsize=(20,20)) #polar plot

    g = np.arange(0,2*np.pi+0.1,0.1)
    h = 2028*np.ones(g.size)
    ax.plot(g,h,linestyle="--",color="gray",label="Edge of FoV")

    for i in altitudes:
        altits = i*np.ones(PAs.size) #makes array of altitudes that are all the same and has length equal to PAs

        if args.cfunc=="constant":
            rrr = fdict[args.rfunc](i,AR_results[0][0],AR_results[0][1],AR_results[0][2],AR_results[0][3])
            #converts the same altitude at each value of theta to a radial value using the fit above
            rrr *= np.ones(PAs.size)
            ax.scatter(PAs*(180/np.pi), rrr,label=str(i))
            #plots the r values for each theta value
        else:
            rrr = newfunc([i,PAs],AR_results[0][0],AR_results[0][1],AR_results[0][2],AR_results[0][3],
            AR_results[0][4],AR_results[0][5],AR_results[0][6],AR_results[0][7],
            AR_results[0][8],AR_results[0][9],AR_results[0][10],AR_results[0][11],
            AR_results[0][12],AR_results[0][13],AR_results[0][14],AR_results[0][15])
            ax.scatter(PAs*(180/np.pi), rrr,label=str(i))


    ax.set_ylim([0,2300]) #set max to half image width
    ax.grid(True)
    plt.legend()
    ax.set_title("Lines of increasing altitude", va='bottom')
    plt.show()
