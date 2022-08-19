#### The necessary Hardware, Directories, Files, and Python Packages needed to run capture-v0.8.py
##### All avalible in capture-v0.8.zip

Hardware:
- Raspberry Pi running bullseye with legacy camera support enabled
- Raspberry Pi HQ camera

Directories:
- dome-templates (contains images of features of the dome which it the script will try to detect)
- out (to save output from script to)

Files:
- Cfunctions.py (in base dir)
- chars.npy (in base dir)
- hflr-template1.jpg (in dome-templates dir; specificaly for murdoc skyWATCH)
- hflr-template2.jpg (in dome-templates dir; specificaly for murdoc skyWATCH)

Python Packages:
- cv2 (openCV for python)
- exif
- gc
- glob
- json
- numpy
- os
- skyfield
- subprocess
- time

