#!/usr/bin/python3.9
from calendar import c
from sre_parse import FLAGS
from tkinter import Y
from typing import Counter
import cv2
from picamera.array import PiRGBArray
from picamera import PiCamera
from threading import Thread
import time
import numpy as np
import PySimpleGUI as sg
import configparser
from networktables import NetworkTables
import sys

DEBUG_MODE = False
DEFAULT_PARAMETERS_FILENAME = "default-params.ini"
PARAMETERS_FILENAME = "st_joe_playoff"
LOAD_FILE = True
HORIZONTAL_FOV = 90
# From refernce drawing:
# https://www.uctronics.com/arducam-90-degree-wide-angle-1-2-3-m12-mount-with-lens-adapter-for-raspberry-pi-high-quality-camera.html
# arctan (4.92/2) /3.28 = 36.86989765, for half the verical
# then 2x for the full veritcal => 36.86989765 * 2 = 73.7397953 => 74 
VERTICAL_FOV = 74
PIXEL_WIDTH = 800
PIXEL_HEIGHT = 600
HORIZONTAL_PIXEL_CENTER = (PIXEL_WIDTH / 2) - 0.5
VERTICAL_PIXEL_CENTER = (PIXEL_HEIGHT / 2) - 0.5 
HORIZONTAL_DEGREES_PER_PIXEL  = HORIZONTAL_FOV / PIXEL_WIDTH 
VERTICAL_DEGREES_PER_PIXEL = VERTICAL_FOV / PIXEL_HEIGHT
RIO_IP = "10.9.10.2"
REMOVE_ENDS_FROM_5 = False
X_PIXEL_ADJUSTMENT = 0
Y_PIXEL_ADJUSTMENT = 0
SHOOTER_FILTER_Y_MAX = 140

def look_up_distance_y(y_pixel):
    return(0)

def look_up_distance_x(x_width):
    return(0)
    
def calc_horizontal_angle_of(x_pixel):
    return (x_pixel - HORIZONTAL_PIXEL_CENTER) * HORIZONTAL_DEGREES_PER_PIXEL

def calc_vertical_angle_of(y_pixel):
    return (y_pixel - VERTICAL_PIXEL_CENTER) * VERTICAL_DEGREES_PER_PIXEL


def find_min_x(contours):
    min_x = 999
    min_x_index = -1
    c_index = -1

    for c in range(len(contours)):
        if cv2.contourArea(contours[c]) > 10:
            for p in range(len(contours[c])):
                for x,y in (contours[c][p]):
                    if ( x < min_x):
                        min_x = x
                        min_x_index = p
                        c_index = c

    return c_index, min_x_index

def find_max_x(contours):
    max_x = -1
    max_x_index = -1
    c_index = -1

    for c in range(len(contours)):
        if cv2.contourArea(contours[c]) > 10:
            for p in range(len(contours[c])):
                for x,y in (contours[c][p]):
                    if ( x > max_x):
                        max_x = x
                        max_x_index = p
                        c_index = c

    return c_index, max_x_index

def find_min_y(contours):
    min_y = 999
    min_y_index = -1
    c_index = -1

    for c in range(len(contours)):
        for p in range(len(contours[c])):
            for x,y in (contours[c][p]):
                if ( y < min_y):
                    min_y = y
                    min_y_index = p
                    c_index = c

    return c_index, min_y_index

def find_max_y(contours):
    max_y = -1
    max_y_index = -1
    c_index = -1

    for c in range(len(contours)):
        for p in range(len(contours[c])):
            for x,y in (contours[c][p]):
                if ( y > max_y):
                    max_y = y
                    max_y_index = p
                    c_index = c

    return c_index, max_y_index

def callback(pos):
    pass

def read_color():
    # reading the current colour value ranges
    hue1 = cv2.getTrackbarPos("H1","app config")
    sat1 = cv2.getTrackbarPos("S1","app config")
    value1 = cv2.getTrackbarPos("V1","app config")
    hue2 = cv2.getTrackbarPos("H2","app config")
    sat2 = cv2.getTrackbarPos("S2","app config")
    value2 = cv2.getTrackbarPos("V2","app config")
    return(hue1, sat1, value1, hue2, sat2, value2)

# for writing parameters file to be used upon next run
def write_params_file(file):
    print("Writing parameter file " + file)
    config = configparser.ConfigParser()
    config.add_section('params_section')
    config['params_section']['H1'] = str(cv2.getTrackbarPos("H1","app config"))
    config['params_section']['S1'] = str(cv2.getTrackbarPos("S1","app config"))
    config['params_section']['V1'] = str(cv2.getTrackbarPos("V1","app config"))
    config['params_section']['H2'] = str(cv2.getTrackbarPos("H2","app config"))
    config['params_section']['S2'] = str(cv2.getTrackbarPos("S2","app config"))
    config['params_section']['V2'] = str(cv2.getTrackbarPos("V2","app config"))
    config['params_section']['min cargo area'] = str(cv2.getTrackbarPos("min cargo area","app config"))
    with open(file, 'w') as configfile:
        config.write(configfile)

def process_user_key(img):
    #if Esc key is pressed exit program
    key = cv2.waitKey(1)
    if (key == 27):
        return True
    elif (key == 119): # if 'w' key save values 
        values_file = sg.popup_get_file("parameters")
        if not values_file:
            values_file = DEFAULT_PARAMETERS_FILENAME 
        write_params_file(values_file)
        return False
    elif (key == 109):
        cv2.imwrite("mask.jpg", img)
        return False
    else:
        return False 

def read_params_file(file):
    print("reading parameter file " + file)
    config = configparser.ConfigParser()
    with open(file, 'r') as configfile:
        config.read_file(configfile)
    
    hue1 = config['params_section']['H1']
    cv2.setTrackbarPos("H1","app config",int(hue1))
    sat1 = config['params_section']['S1']
    cv2.setTrackbarPos("S1","app config",int(sat1))
    value1 = config['params_section']['V1']
    cv2.setTrackbarPos("V1","app config",int(value1))
    hue2 = config['params_section']['H2']
    cv2.setTrackbarPos("H2","app config",int(hue2))
    sat2 = config['params_section']['S2']
    cv2.setTrackbarPos("S2","app config",int(sat2))
    value2 = config['params_section']['V2']
    cv2.setTrackbarPos("V2","app config",int(value2))
    area = config['params_section']['min cargo area']
    cv2.setTrackbarPos("min cargo area","app config",int(area))

def output_data(loops,current_time,calc_time,cam_distance,cam_angle_of_horizontal,color):
    # data format for network table key "Target" : "id,current time,calcuated time,distance,angle of,color"
    hub_data = "%d,%8.3f,%8.3f,%8.3f,%8.3f,%d" % (loops,current_time,calc_time,cam_distance,cam_angle_of_horizontal,color)
    nt.putString("Target",hub_data)

    if DEBUG_MODE == True:
        print( hub_data)

def draw_target(img,x,y):

    if DEBUG_MODE == True:
        #print(pts)
        img = cv2.circle(img, (x,y), 8, (0,0,255), -1)

    return(img)

class PiVideoStream: # from pyimagesearch
    def __init__(self, resolution=(PIXEL_WIDTH, PIXEL_HEIGHT), framerate=40, brightness=54, \
        contrast=100, sharpness=100, exposure_compensation=-18, saturation=100):
        # initialize the camera and stream
        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.framerate = framerate
        self.camera.brightness = brightness # between 0 and 100 (50 is default)
        self.camera.contrast = contrast # between -100 and 100 (0 is default)
        self.camera.sharpness = sharpness # between -100 and 100 (0 is default)
        self.camera.exposure_compensation = exposure_compensation # Each increment represents 1/6th of a stop. -25 and 25 (0 is default)
        self.camera.saturation = saturation #-100 to 100 (0 is default)
        self.camera.awb_mode = 'cloudy'
        #self.camera.exposure_mode = 'beach'
        self.rawCapture = PiRGBArray(self.camera, size=resolution)
        self.stream = self.camera.capture_continuous(self.rawCapture,
            format="bgr", use_video_port=True)
        # initialize the frame and the variable used to indicate
        # if the thread should be stopped
        self.frame = None
        self.stopped = False
    def start(self):
        # start the thread to read frames from the video stream
        Thread(target=self.update, args=()).start()
        return self
    def update(self):
        # keep looping infinitely until the thread is stopped
        for f in self.stream:
            # grab the frame from the stream and clear the stream in
            # preparation for the next frame
            self.frame = f.array
            self.rawCapture.truncate(0)
            # if the thread indicator variable is set, stop the thread
            # and release camera resources
            if self.stopped:
                self.stream.close()
                self.rawCapture.close()
                self.camera.close()
                return
    def read(self):
        # return the frame most recently read
        return self.frame
    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True
    def set_brightness(self,setting):
        self.camera.brightness = setting
        time.sleep(3)
    def set_contrast(self,setting):
        self.camera.contrast = setting
        time.sleep(3)
    def set_exposure(self,setting):
        self.camera.exposure = setting
        time.sleep(3)
    def set_sharpness(self,setting):
        self.camera.sharpness = setting
        time.sleep(3)
    def set_saturation(self,setting):
        self.camera.saturation = setting
        time.sleep(3)

def show_x_and_y(event, x, y, flags, userdata):
    if event == cv2.EVENT_LBUTTONDOWN:
        print('({x},{y})'.format(x=x,y=y))

# START

# determine debug mode depending on how the program was run
if len(sys.argv) == 2 and sys.argv[1] == "debug":
    DEBUG_MODE = True
else:
    DEBUG_MODE = False

# create window with trackbars to control the color range
cv2.namedWindow("app config")
cv2.resizeWindow("app config",600,800)
cv2.createTrackbar("H1","app config",0,180,callback)
cv2.createTrackbar("S1","app config",0,255,callback)
cv2.createTrackbar("V1","app config",0,255,callback)
cv2.createTrackbar("H2","app config",0,180,callback)
cv2.createTrackbar("S2","app config",0,255,callback)
cv2.createTrackbar("V2","app config",0,255,callback)
cv2.createTrackbar("min cargo area","app config",0,500,callback)

read_params_file(PARAMETERS_FILENAME)

NetworkTables.initialize(RIO_IP)
NetworkTables.setUpdateRate(0.010)
nt = NetworkTables.getTable("pi")

vs = PiVideoStream().start() # create camera object and start reading images
print ("starting stream")
time.sleep(3) # camera sensor settling time

callback_set = False

loops = 0


while True:

  # start with robot time then add processing time at the end
    start_time_robot = nt.getNumber("RobotTime",0)
    start_time_pi = time.process_time()
    
    nt.putNumber("PiTime",start_time_pi)

    image = None
    mask = None

    # read an image from the camara
    # camera is mounted upside down, so the image needs to be flipped around the x-axis
    flipped_image = vs.read()
    image = cv2.flip(flipped_image,0)

    # convert the image HSV for colour checking
    hsv = cv2.cvtColor(image,cv2.COLOR_BGR2HSV)

    # read current color ranges
    (h1,s1,v1,h2,s2,v2) = read_color()

    # min_cargo_area = cv2.getTrackbarPos("min cargo area","app config")

    # convert color value ranges into array 
    color1 = np.array([h1,s1,v1])
    color2 = np.array([h2,s2,v2])  
    # identify the color by checking the pixel
    mask = cv2.inRange(hsv,color1,color2)
    cv2.imshow("Mask",mask)
    
    # kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(3,3))
    # cleaner_mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    raw_contours,_ = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    #cv2.drawContours(image, raw_contours, -1, (0,255,0), 3)

    l = len(raw_contours)
    print(l)

    if (l > 2 and l < 20):

        min_top_list = []

        for c in raw_contours:
            if(cv2.contourArea(c) > 15):
                x,y,w,h = cv2.boundingRect(c)
                if (w > h):
                    #see extreme points in open cv contour properties documentation
                    min_top = tuple(c[c[:,:,1].argmin()][0])
                    if (min_top[1] > SHOOTER_FILTER_Y_MAX):
                        min_top_list.append(min_top)
        
        if (len(min_top_list) > 0):
            min_top_x = 0
            min_top_y = 999
            for point in min_top_list:
                if point[1] < min_top_y:
                    min_top_y = point[1]
                    min_top_x = point[0]

            cam_distance = look_up_distance_y(min_top_y) #  y-coordinate of top most
            cam_angle_of_horizontal = calc_horizontal_angle_of(min_top_x) # x-coordinate of top most

            # loop time
            end_time_pi = time.process_time()
            calc_time = end_time_pi - start_time_pi
            loops = loops + 1
            output_data(loops,start_time_robot,calc_time,0,cam_angle_of_horizontal,0)
            
            image = draw_target(image, min_top_x, min_top_y)

    # update all the images
    cv2.imshow("RPiVideo",image)
    cv2.imshow("Mask",mask)
    #cv2.imshow("Clean Mask",cleaner_mask)

    if(callback_set == False):
        cv2.setMouseCallback("RPiVideo", show_x_and_y)
        callback_set = True

    if process_user_key(mask) == True:
        break
        
# cleanup
cv2.destroyAllWindows()
vs.stop()