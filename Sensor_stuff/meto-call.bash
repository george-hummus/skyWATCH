#! /usr/bin/bash

while :
do
        python meto-read.py
        date >> meto-info.txt
        ./gdrive update 1pVC5xfZPMt_sPCmpAKIDPzxxuti3xnMO meto-info.txt
        sleep 600
done
