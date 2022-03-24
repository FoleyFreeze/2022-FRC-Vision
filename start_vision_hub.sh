#!/bin/bash
#
cd /home/pi/2022-FRC-Vision
echo "starting vision hub"
sleep 3
python3 vision_hub.py debug
echo "ending vision hub"
sleep 3
exit