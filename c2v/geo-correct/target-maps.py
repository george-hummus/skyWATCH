#imports
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
import argparse

#command line arguments
parser = argparse.ArgumentParser(description = """
Creates map of the target stars on top of thier corresponding image (sky-map image or all-sky image), which can be used to check the star coordinates are correct.
Author: George Hume
2022
""")
#adding arguments to praser object
parser.add_argument('targets' , type = str, help = "Path to the CSV file with the coordinates of the target stars in the sky-map (x,y) and the all-sky image (x',y')")
parser.add_argument('SMim' , type = str, help = "Path to the sky-map image.")
parser.add_argument('ASim' , type = str, help = "Path to the all-sky image.")
parser.add_argument('--ext' , type = str, help = 'Image file type the outputs will be saved as. Supports PNG (default), JPEG and BMP.', default = "png")
args = parser.parse_args()

#load in images
smim = cv.imread(args.SMim) #sky-map
asim = cv.imread(args.ASim) #all-sky

#load in the coordinates from CSV file (excluding the column titles)
coords = np.loadtxt(args.targets,delimiter=",",skiprows=1,dtype=int)
x,y = coords.T[1], coords.T[2] #x and y for sky-map are in 2nd and 3rd columns
x1, y1 = coords.T[3], coords.T[4] #x and y for all-sky image are in 4th and 5th columns

#removes any blank entries with masks
x = x[np.where(x!=0)]
y = y[np.where(y!=0)]
x1 = x1[np.where(x1!=0)]
y1 = y1[np.where(y1!=0)] #make sure no targets have coordinates of zero!

#makes the sky-map verison
fig1, ax1 = plt.subplots()
ax1.imshow(cv.cvtColor(smim, cv.COLOR_BGR2RGB))
ax1.scatter(x,y,alpha=0.5,c="r")
fig1.savefig(f'SM-targets.{args.ext}',dpi=600)

#makes the all-sky verison
fig2, ax2 = plt.subplots()
ax2.imshow(cv.cvtColor(asim, cv.COLOR_BGR2RGB))
ax2.scatter(x1,y1,alpha=0.5,c="r")
fig2.savefig(f'AS-targets.{args.ext}',dpi=600)
