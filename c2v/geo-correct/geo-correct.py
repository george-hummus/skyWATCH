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
parser.add_argument('cords' , type = str, help = 'Path to the CSV file containing the coordinates of corresponding stars in the all-sky image and sky-map.')
parser.add_argument('--ASimage' , type = str, help = 'Path to the all-sky image file, if you want transformation to be applied to it at the end. By default this this will not occur', default = "None")

#load in a csv file with x,y points from all-sky image and x',y' points from the skymap for target stars
coords=np.loadtxt("star-cords.csv",delimiter=",",dtype="int")
x = coords[0]
y = coords[1]
x1 = coords[2]
x2 = coords[3]

#do polynomial least fit to find warping coefficents of the X and Y transformation matrices

#need to save the transformation matrix so it can be used again.

#option to apply transformation matrix on each point of the all-sky image to correct it
if args.ASimage != "None":

else:
    exit()
