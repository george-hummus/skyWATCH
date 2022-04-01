#! /usr/bin/bash

python meto-plots.py &

while :
do
        con=0 #resets con to zero
        ping -c 1 google >/dev/null && ((con++)) #if we can ping google bish set to 1
        if [ $con -eq 0 ]; then #if con still zero we couldn't ping
          break #so we break the loop
        fi

        sleep 600 #waits for first cycle of meto-plots.py to finish

        #sending out ip-addresss
        ifconfig > ip_address.txt
        date >> ip_address.txt
        ./gdrive update 1sFXZ7Dj6GFhmnydgR5fWS9YsKNy_cYFs ip_address.txt

        #sending out current meto readings
        python meto-read.py
        date >> meto-info.txt
        ./gdrive update 1pVC5xfZPMt_sPCmpAKIDPzxxuti3xnMO meto-info.txt

        #sending out new plot
        ./gdrive update 1JeAZm0XsRS7Qevb_4v5hZKqyS08qRW0q meto-plots.png

done

echo "internet connection lost" > errors.txt #if loose connection this is saved
date >> errors.txt
