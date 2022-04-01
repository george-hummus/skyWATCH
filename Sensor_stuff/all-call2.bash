#! /usr/bin/bash
while :
do
  counter=0 #initalises counter
  current_dir=$(date +%Y%m%d) #need to save this at start as at end of day when moving files the date will have chnaged.
  mkdir meto_out/$current_dir #makes directory with the date
  echo "start day"
  until [ $counter -eq 144 ] #144 new plots per day
  do

    #ip_address uplaod
    ifconfig > ip_address.txt
    date >> ip_address.txt
    ./gdrive update 1sFXZ7Dj6GFhmnydgR5fWS9YsKNy_cYFs ip_address.txt || "failed to upload ip-address" >> errors.txt ;  date >> errors.txt

    #meto text upload
    python meto-read.py
    date >> meto-info.txt
    ./gdrive update 1pVC5xfZPMt_sPCmpAKIDPzxxuti3xnMO meto-info.txt ||  "failed to upload current meto info" >> errors.txt ; date >> errors.txt

    #meto plots
    python meto_plots.py #sleep is within here

    ((counter++)) #increments counter
  done

  #moves the outputs from plotting into the directory of the date at end of day
  mv meto_out/meto-plots.png meto_out/$current_dir
  mv meto_out/data.csv meto_out/$current_dir

  ./gdrive upload -r meto_out/$(date +%Y%m%d) || "failed to upload plots and results" >> errors.txt ;  date >> errors.txt
done
