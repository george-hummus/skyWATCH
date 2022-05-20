# skyWATCH
#### This respository contains prototype code which is being used to create RaspberryPi all-in-one all-sky camera and weather station for use at the Observatory Roque de la Muchachos. 

Directory Guide:
- Sensor_stuff: contains code being trialed for weather monitoring with the BME280 Environmental Sensor
- c2v: cotains code being trialed for the image capture and post-processing of the all-sky camera (e.g., cloud detection, sky-map overlays, etc.)
  - distortion: code for finding distortion parameters of the all-sky camera sensor and lens.
  - geo-correct: the distortion method was not effective, so have moved to a method of geometric correction of the image using polynomial warping.
- picam: contains test code for conrolling the Raspberry Pi High Quality Camera which can de depolyed as the all-sky camera in the skyWATCH devices.
- astro-info: a script which uses python package Skyfield to find the position of the sun and moon, so the astronomical conditions can be recoreded into a JSON file.

