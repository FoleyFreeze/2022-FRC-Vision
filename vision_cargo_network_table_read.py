#!/usr/bin/python3.9
from audioop import reverse
from distutils.debug import DEBUG
from operator import itemgetter
import cv2
from picamera.array import PiRGBArray
from picamera import PiCamera
from threading import Thread
import time
import numpy as np
import PySimpleGUI as sg
import configparser
import sys
from enum import Enum
from networktables import NetworkTables
import math
import RPi.GPIO as GPIO

RIO_IP = "10.9.10.2"
DEFAULT_PARAMETERS_FILENAME = "default-params.ini"

# for writing parameters file to be used upon next run and puts parameters in network table pi
def write_params_file(file):
    print("Writing parameter file " + file)
    config = configparser.ConfigParser()
    config.add_section('params_section')
    config['params_section']['blue H1'] = str(nt.getString("blue H1", "0"))
    config['params_section']['blue S1'] = str(nt.getString("blue S1", "0"))
    config['params_section']['blue V1'] = str(nt.getString("blue V1", "0"))
    config['params_section']['blue H2'] = str(nt.getString("blue H2", "0"))
    config['params_section']['blue S2'] = str(nt.getString("blue S2", "0"))
    config['params_section']['blue V2'] = str(nt.getString("blue V2", "0"))
    config['params_section']['red H1'] = str(nt.getString("red H1", "0"))
    config['params_section']['red S1'] = str(nt.getString("red S1", "0"))
    config['params_section']['red V1'] = str(nt.getString("red V1", "0"))
    config['params_section']['red H2'] = str(nt.getString("red H2", "0"))
    config['params_section']['red S2'] = str(nt.getString("red S2", "0"))
    config['params_section']['red V2'] = str(nt.getString("red V2", "0"))
    config['params_section']['aspect ratio min'] = str(nt.getString("aspect ratio min", "0"))
    config['params_section']['aspect ratio max'] = str(nt.getString("aspect ratio max", "0"))
    config['params_section']['extent max'] = str(nt.getString("extent max", "0"))
    config['params_section']['gamma'] = str(nt.getString("gamma", "0"))

    with open(file, 'w') as configfile:
        config.write(configfile)
        print("Wrote parameter file " + file)

# START

# determine debug mode depending on how the program was run
if len(sys.argv) == 2:

    params_file_name = sys.argv[1] 

elif len(sys.argv) == 1:

    params_file_name = DEFAULT_PARAMETERS_FILENAME 

else:

    sys.exit("invalid command line")

NetworkTables.initialize(RIO_IP)
NetworkTables.setUpdateRate(0.010)
nt = NetworkTables.getTable("pi")

time.sleep(3)

write_params_file(params_file_name)