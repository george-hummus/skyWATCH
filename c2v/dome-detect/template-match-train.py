#IMPORTS
import cv2 as cv
import numpy as np
import glob
import csv
from tqdm import tqdm

imgs = glob.glob('/media/george/Work/skyWATCH/dome-test-imgs/*.jpg')
temps = glob.glob('dome-templates/hf**.jpg') #loads in templates

f = open('temp-train/results.csv', 'w')
writer = csv.writer(f, delimiter=',',
                        quotechar='|', quoting=csv.QUOTE_MINIMAL)
writer.writerow(['Image Name', 'predicted x-value', 'predicted y-value','Exceed threshold?'])

th = 150 #cut-off threshold

for i in tqdm(imgs):
    img = cv.imread(i,0)

    #highlight dome fetures
    img = np.invert(cv.equalizeHist(img)).clip(min=th)
    #histogram flattener normalises the brightness of the images

    img2 = img.copy()

    img = img2.copy()
    method = eval('cv.TM_CCOEFF')

    results = []
    limsx = [[2910,2940],[805,825]]
    limsy = [[205,225],[610,640]]

    for j in range(2): # 2 templates to match (either can match for +ve result)
        template = cv.imread(temps[j],0)
        w, h = template.shape[::-1]

        # Apply template Matching
        res = cv.matchTemplate(img,template,method)
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)

        #checks if predicted location of template in image is within x pixels of the true position (if not then its likely the dome is open)
        if (max_loc[0] > limsx[j][0]) & (max_loc[0] < limsx[j][1]):
            if (max_loc[1] > limsy[j][0]) & (max_loc[1] < limsy[j][1]):
                results.append(True)
            else:
                results.append(False)
        else:
            results.append(False)

    result = results[0] or results[1]

    writer.writerow([i[43:], max_loc[0], max_loc[1], result])

f.close()
