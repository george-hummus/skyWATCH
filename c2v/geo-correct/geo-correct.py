#### NOT FINISHED ####
exit()

### IMPORTS ###
import cv2 as cv
import numpy as np
import argparse
import os

#command line arguments
parser = argparse.ArgumentParser(description = """
Takes collection of coordinates of stars in an all-sky image and sky-map, and uses these to calculate a transformation matrix for the all-sky image. This can then be applied to all all-sky images so constellation overlay can be applied to it.
Author: George Hume
2022
""")
#adding arguments to praser object
parser.add_argument('coords' , type = str, help = 'Path to the CSV file containing the coordinates of corresponding stars in the all-sky image and sky-map.')
parser.add_argument('--ASimage' , type = str, help = 'Path to the all-sky image file, if you want transformation to be applied to it at the end. By default this this will not occur', default = "None")

#load in a csv file with x,y points from all-sky image and x',y' points from the skymap for target stars
coords=np.loadtxt(args.coords,delimiter=",",dtype="int",skiprows=1)
x,y = coords.T[1], coords.T[2] #x and y for sky-map are in 2nd and 3rd columns
x1, y1 = coords.T[3], coords.T[4] #x and y for all-sky image are in 4th and 5th columns

#remove targets which don't appear on all-sky image (marked with zeros, make sure no targets have coordinates of zero!)
unmatch = x1!=0 #mask
#apply mask to x,y,x',y'
x = x[unmatch]
y = y[unmatch]
x1 = x1[unmatch]
y1 = y1[unmatch]

#do polynomial least fit to find warping coefficents of the X and Y transformation matrices

#need to save the transformation matrix so it can be used again.

#option to apply transformation matrix on each point of the all-sky image to correct it
if args.ASimage != "None":

else:
    exit()
