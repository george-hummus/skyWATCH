"""
Overlays constellation map onto an all-sky image, by distorting it to match the all-sky image lens/camera distortion.
Author: George Hume
2022
"""

### IMPORTS ###
import cv2 as cv
import numpy as np
import imgkit
import argparse
import os

#command line arguments
parser = argparse.ArgumentParser(description = """
Overlays constellation map onto an all-sky image, by distorting it to match the all-sky image lens/camera distortion.
Author: George Hume
2022
""")
#adding arguments to praser object
parser.add_argument('path' , type = str, help = 'Path to the all-sky image file, needs to be landscape.')
parser.add_argument('camPars' , type = str, help = 'Path to the camera parameter NPZ file.')
parser.add_argument('lat' , type = float, help = 'Lattitude the all-sky image was taken.')
parser.add_argument('long' , type = float, help = 'Longitude the all-sky image was taken.')
parser.add_argument('date' , type = str, help = 'Date and time the all-sky image was taken. Format: mmm dd yyyy hh:mm:ss (UTC) (e.g., "Apr 01 2022 00:00:00").')
parser.add_argument('--out_dir' , type = str, help = "Path to directory files will be saved to. If doesn't exist it will be created.", default = "overlay_out")
parser.add_argument('--ext' , type = str, help = 'Image file type the outputs will be saved as. Supports PNG (default), JPEG and BMP.', default = "png")
args = parser.parse_args()

#check date format, as it has to be exact
if (args.date[3] == args.date[6] == args.date[11] == " ") & (args.date[14] == args.date[17] == ":"):
    print("start")
else:
    print('ERROR: wrong date format, use "mmm dd yyyy hh:mm:ss" in UTC, e.g., "Apr 01 2022 00:00:00"')
    exit()

#reads image of sky
sky = cv.imread(args.path)

#makes directory to save output to if not already there
if os.path.isdir(args.out_dir) == False:
    os.mkdir(args.out_dir) #if no dir of same name it creates it
    out_path = f"{args.out_dir}/"
else:
    out_path = f"{args.out_dir}/"

#make html file to grab a skymap for given lat, long and date
lat = str(args.lat)
long = str(args.long)
dt = f"%20{args.date[0:3]}%20{args.date[4:6]}%20{args.date[7:11]}%20{args.date[12:20]}%20UTC"
html_map = f'<iframe width="1000" height="1000" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" src="https://virtualsky.lco.global/embed/index.html?longitude={long}&latitude={lat}&gradient=false&projection=polar&mouse=false&keyboard=false&constellations=true&constellationlabels=true&showstars=false&showdate=false&showposition=false&clock={dt}" allowTransparency="true"></iframe>'
with open(f'{out_path}map_{lat}{long}.html', 'w') as file:
    file.write(html_map)

#turns html file into image
imgkit.from_file(f'{out_path}map_{lat}{long}.html', f'{out_path}map_{lat}{long}.{args.ext}')
map = cv.imread(f'{out_path}map_{lat}{long}.{args.ext}')

#crop image so no boarders
map = map[8:1008,8:1008]

#load distortion parameters
c_pars = np.load(args.camPars)
ret, mtx, dist, rvecs, tvecs = c_pars['arr_0'], c_pars['arr_1'], c_pars['arr_2'], c_pars['arr_3'], c_pars['arr_4']

#lets distort the sky map
h,w = map.shape[:2]
dist_u = np.negative(dist)   #inverse distortion matrix
new_camera_mtx_inv, roi = cv.getOptimalNewCameraMatrix(mtx, dist_u, (w, h), 1, (w, h))
#new cam matrix for reverse dist
distorted_map = cv.undistort(map, mtx, dist_u, None, new_camera_mtx_inv) #redistort

x, y = sky.shape[1], sky.shape[0]
map_ol = cv.resize(distorted_map, [x,x]) #resize map to be same width as sky image
lower = int((x-y)/2) #indices so crop is at centre of image
map_ol =  map_ol[lower:lower+y] #crop the distored map so it has same dimensions as sky
skyblend = cv.addWeighted(sky,0.7,map_ol,0.2,0)
