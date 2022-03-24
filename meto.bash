#! /usr/bin/bash
while :
do
  counter=0 #initalises counter
  mkdir meto_out/$(date +%Y%m%d) #makes directory with the date
  echo "start day"
  until [ $counter -eq 144 ] #144 new plots per day
  do

    python meto-plots2.py

    ((counter++)) #increments counter
    sleep 600 #get a reading every 10mins
  done
  #moves the outputs into the directory of the date at end of day
  mv meto_out/meto-plots.png meto_out/$(date +%Y%m%d)
  mv meto_out/data.csv meto_out/$(date +%Y%m%d)

  ./gdrive upload -r meto_out/$(date +%Y%m%d) || errors.txt >> "failed to upload" ; errors.txt >> date
done
