#!/bin/bash
#
cd /home/pi/2022-FRC-Vision
echo "starting vision cargo"
sleep 3
python3 vision_cargo.py debug output left
echo "ending vision cargo"
sleep 3
exit