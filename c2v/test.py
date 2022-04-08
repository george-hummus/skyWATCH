#IMPORTS
import cv2 as cv
import numpy as np
import argparse

#sys arguments
parser = argparse.ArgumentParser(description = "Overlays two images using openCV.")
parser.add_argument('im1' , type = str, help = 'Path to the first image file.')
parser.add_argument('im2' , type = str, help = 'Path to the second image file.')
args = parser.parse_args()

#load in images
img1 = cv.imread(args.im1)
img2 = cv.imread(args.im2)

w, h = img1.shape[1], img1.shape[0] #heigth and width of first image

img2 = cv.resize(img2, [w,h]) #resize image 2 to match that of first

blend = cv.addWeighted(img1,0.5,img2,0.5,0) #overlays images with equal calibration

cv.imwrite('blend.png', blend) #saves overlaid image as png
