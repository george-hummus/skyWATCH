#! /usr/bin/bash

while :
do
        ifconfig > ip_address.txt
        date >> ip_address.txt
        ./gdrive update 1sFXZ7Dj6GFhmnydgR5fWS9YsKNy_cYFs ip_address.txt
        sleep 600
done
