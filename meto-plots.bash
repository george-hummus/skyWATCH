#! /usr/bin/bash

python meto-plots.py &

while :
do
        sleep 600
        ./gdrive update 1JeAZm0XsRS7Qevb_4v5hZKqyS08qRW0q meto-plots.png
done
