#imports
import cv2 as cv
import numpy as np
import imgkit
import argparse
import json
import os

#command line arguments
parser = argparse.ArgumentParser(description = """
Creates sky map at the same position and time as an all-sky image with the same dimensions, which will be used for geometric correction of the all-sky image.
Author: George Hume
2022
""")
#adding arguments to praser object
parser.add_argument('path' , type = str, help = 'Path to the JSON information file for the all-sky image file.')
parser.add_argument('--ext' , type = str, help = 'Image file type the outputs will be saved as. Supports PNG (default), JPEG and BMP.', default = "png")
args = parser.parse_args()

#load in lat, long, and date from JSON
with open(args.path, 'r') as j:
     skyinfo = json.loads(j.read()) #loads in the json as a dict

#height and width of sky image
h = skyinfo["height"]
w = skyinfo["width"]

#lattitude and longitude
lat = str(skyinfo["location"]["latitude"])
long = str(skyinfo["location"]["longitude"])

#time needs to be formatted just right otherwise you get a blank screen
date = skyinfo["date"]
#extracts each component of the date from the date string
dd = date[8:10] #day
mm = date[5:7] #month
yyyy = date[0:4] #year
HH = date[11:13] #hour
MM = date[14:16] #mins
SS = date[17:19] #secs
#need to convert the month into its 2 letter nanme
months = {"01":"Jan","02":"Feb","03":"Mar","04":"Apr","05":"May","06":"Jun","07":"Jul","08":"Aug","09":"Sep","10":"Oct","11":"Nov","12":"Dec"} #dict of months
mmm = months[mm]
clock = f"%20{mmm}%20{dd}%20{yyyy}%20{HH}:{MM}:{SS}%20UTC"

#creates the map from html
html_map = f'<iframe width="1000" height="1000" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" src="https://virtualsky.lco.global/embed/index.html?longitude={long}&latitude={lat}&gradient=false&projection=polar&mouse=false&keyboard=false&cardinalpoints=false&showplanetlabels=false&showdate=false&showposition=false&clock={clock}" allowTransparency="true"></iframe>'
map_name = f'map_{yyyy}{mm}{dd}{HH}{MM}{SS}'
with open(f'{map_name}.html', 'w') as file:
    file.write(html_map) #saves string as html file

#turns html file into image
imgkit.from_file(f'{map_name}.html', f'{map_name}.{args.ext}')


#editing the skymap image to be the same size as the all-sky image
map = cv.imread(f'{map_name}.{args.ext}') #imports image using openCV
map = map[8:1008,8:1008] #crop image so no boarders
map = cv.resize(map, [w,w]) #resize map to be same width as sky image
lower = int((w-h)/2) #indices so crop is at centre of image
map =  map[lower:lower+h] #crop the distored map so it has same dimensions as sky

#saves the final map (overwrites the original prodcued)
cv.imwrite(f'{map_name}.{args.ext}',map)
