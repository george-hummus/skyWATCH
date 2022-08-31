import numpy as np
import matplotlib.pyplot as plt
import argparse
from Pfunctions import *
import json
from PIL import Image

#command line arguments
parser = argparse.ArgumentParser(description = """
Uses the paramters from the fitting to predict the location of stars in a reference image from the same device and compares this with their real positions.
Author: George Hume
2022
""")
#adding arguments to praser object
parser.add_argument('test_path' , type = str, help = 'Path to the CSV file containing the test sources.')
parser.add_argument('json_path' , type = str, help = 'Path to the JSON file containing the fit paramters and device info.')
parser.add_argument('image_path' , type = str, help = 'Path to the image the test stars are from.')
args = parser.parse_args()


#open json and unpack
with open(args.json_path, 'r') as f:
    prams = json.load(f)

TAinfo = prams["theta-az fit"]
RAinfo = prams["r-alt fit"]
dinfo = prams["device info"]


#load in the test stars and the image
testsky = Image.open(args.image_path)
realpos = np.loadtxt(args.test_path,delimiter=",",usecols = (1,2),skiprows=1)
testnames = np.loadtxt(args.test_path,delimiter=",",usecols = 0,dtype=str,skiprows=1)
testRA = np.loadtxt(args.test_path,delimiter=",",usecols = (3,4,5),skiprows=1)
testDEC = np.loadtxt(args.test_path,delimiter=",",usecols = (6,7,8),skiprows=1)
testTimes = np.loadtxt(args.test_path,delimiter=",",usecols = 9,skiprows=1,dtype=str)
realX=realpos.T[0]
realY=realpos.T[1]


#convert RA and Dec to Alt and Az of test stars
testALT,testAZ = radec2azalt(testRA,testDEC,testTimes,dinfo["lat"],dinfo["long"],dinfo["elv"])


## dict of possible functions
fdict = {"linear":linear, "quadratic":quadratic, "cubic":cubic, "cosine":cosine}


#use fit to get corrected theta
testTHT = linear(testAZ,TAinfo["fitted coeffients"][0], TAinfo["fitted coeffients"][1],TAinfo["fitted coeffients"][2],TAinfo["fitted coeffients"][3])

#turn corrected theta to theta frame of reference
testTHETA = polar_angle(testTHT)


## get r values
if TAinfo["function"] == "linear":
    testR = fdict[RAinfo["function"]](testALT,RAinfo["fitted coeffients"][0], RAinfo["fitted coeffients"][1],RAinfo["fitted coeffients"][2], RAinfo["fitted coeffients"][3])

else:
    #here do the thing with r(theta,az)
    print("haven't done this yet")
    exit()


#calculate the predicted and real xy coords of the test stars
testX,testY = rt2pcoords(testR,testTHETA)


#delta value
distanceDelta = np.sqrt((realX-testX)**2+(realY-testY)**2) #mean distance between real and predicted
print(f"mean distance delta = {np.mean(distanceDelta)}")


#plot the real postions and the calculated ones
fig = plt.figure(figsize=(10,10))
plt.imshow(testsky)
plt.scatter(realX,realY,color="r",alpha=0.3)
plt.scatter(testX,testY,color="b",alpha=0.3)

for i in range(testnames.size):
    plt.annotate(testnames[i]+"-real",[realX[i],realY[i]],
                 [realX[i],realY[i]-50],color="r",alpha=0.6)
    plt.annotate(testnames[i]+"-predicted",[testX[i],testY[i]],
                 [testX[i],testY[i]-50],color="b",alpha=0.6)

plt.show()
