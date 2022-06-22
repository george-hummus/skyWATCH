from Cfunctions import placeholder, timeplase
import datetime as dt

startT = dt.datetime(2022,6,3,0,0,0,tzinfo=utc)

imagess = []

for i in range(144): #24hr cycle, image every 10mins

    tnow=(startT+dt.timedelta(minutes=i*10))
    t=tnow.strftime("%H:%M:%S")
    tstr=tnow.strftime("%H%M%S")

    imagepath=f"TESTING/PH-test/PH-{tstr}.jpg"

    placeholder("this thingy Q", "nowhere!", t, imagepath)
    logger("TESTING/PH-test/images.list",f"{imagepath}\n")
    imagess.append(imagepath)


timelapse(imagess,"TESTING/PH-test/PH-movie.mp4")
