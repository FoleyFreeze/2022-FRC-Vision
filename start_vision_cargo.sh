#!/bin/bash
#
cd /home/pi/2022-FRC-Vision
sleep 3
python3 vision_cargo.py debug output
echo "ending vision"
sleep 3
exit