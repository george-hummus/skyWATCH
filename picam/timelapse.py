from picamera import PiCamera
from os import system
from time import sleep

camera = PiCamera()

for i in range(180):
    camera.capture('tl/image{0:04d}.jpg'.format(i))
    sleep(300)

system('convert -delay 10 -loop 0 tl/image*.jpg tl/animation.gif')
print('done')
