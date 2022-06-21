## IMPORTS ##
from Cfunctions import timelapse
import argparse
import numpy as np

## SYS ARGUMENTS ##
parser = argparse.ArgumentParser(description = 'Creates a timelapse video from a list of images saved as a CSV file.')
parser.add_argument('list' , type = str, help = 'path to the CSV-type file containing the list of images')
parser.add_argument('opath' , type = str, help = 'Path to which the directory movie will be saved to.')
parser.add_argument('--width' , type = int, help = 'Pixel width of the final movie, default is 825pix.', default = 825)
parser.add_argument('--height' , type = int, help = 'Pixel width of the final movie, default is 640pix.', default = 640)
args = parser.parse_args()

## Read in list of images ##
imlist = np.loadtxt(args.list,dtype=str) #loads in the list as a numpy array

## Creates resolution array ##
reso = [args.width,args.height]

## Creates the movie ##
timelapse(imlist,f"{args.opath}/timeplase.mp4",res=[825,640])
