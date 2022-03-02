#!/usr/bin/python3.9
from audioop import reverse
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

DEFAULT_PARAMETERS_FILENAME = "default-params.ini"
PARAMETERS_FILENAME = "default-params.ini"
ASPECT_RATIO_OF_1_MIN = 0.9
ASPECT_RATIO_OF_1_MAX = 1.05
EXTENT_MIN = 0.0
EXTENT_MAX = 0.8
CARGO_TO_OUTPUT_MAX = 3

class CargoColor(Enum):
    RED = 1
    BLUE = 2

def callback(pos):
    pass

# for writing parameters file to be used upon next run
def write_params_file(file):
    print("Writing parameter file " + file)
    config = configparser.ConfigParser()
    config.add_section('params_section')
    config['params_section']['blue H1'] = str(cv2.getTrackbarPos("blue H1","trackbars"))
    config['params_section']['blue S1'] = str(cv2.getTrackbarPos("blue S1","trackbars"))
    config['params_section']['blue V1'] = str(cv2.getTrackbarPos("blue V1","trackbars"))
    config['params_section']['blue H2'] = str(cv2.getTrackbarPos("blue H2","trackbars"))
    config['params_section']['blue S2'] = str(cv2.getTrackbarPos("blue S2","trackbars"))
    config['params_section']['blue V2'] = str(cv2.getTrackbarPos("blue V2","trackbars"))
    config['params_section']['red H1'] = str(cv2.getTrackbarPos("red H1","trackbars"))
    config['params_section']['red S1'] = str(cv2.getTrackbarPos("red S1","trackbars"))
    config['params_section']['red V1'] = str(cv2.getTrackbarPos("red V1","trackbars"))
    config['params_section']['red H2'] = str(cv2.getTrackbarPos("red H2","trackbars"))
    config['params_section']['red S2'] = str(cv2.getTrackbarPos("red S2","trackbars"))
    config['params_section']['red V2'] = str(cv2.getTrackbarPos("red V2","trackbars"))
    config['params_section']['aspect ratio min'] = str(cv2.getTrackbarPos("aspect ratio min","trackbars"))
    config['params_section']['aspect ratio max'] = str(cv2.getTrackbarPos("aspect ratio max","trackbars"))
    config['params_section']['extent max'] = str(cv2.getTrackbarPos("extent max","trackbars"))
    with open(file, 'w') as configfile:
        config.write(configfile)

def process_user_key():
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
    else:
        return False 

def read_params_file(file):
    print("reading parameter file " + file)
    config = configparser.ConfigParser()
    with open(file, 'r') as configfile:
        config.read_file(configfile)

    return config

def set_trackbar_values(config):
    cv2.setTrackbarPos("blue H1","trackbars",int(config['params_section']['blue H1']))
    cv2.setTrackbarPos("blue S1","trackbars",int(config['params_section']['blue S1']))
    cv2.setTrackbarPos("blue V1","trackbars",int(config['params_section']['blue V1']))
    cv2.setTrackbarPos("blue H2","trackbars",int(config['params_section']['blue H2']))
    cv2.setTrackbarPos("blue S2","trackbars",int(config['params_section']['blue S2']))
    cv2.setTrackbarPos("blue V2","trackbars",int(config['params_section']['blue V2']))

    cv2.setTrackbarPos("red H1","trackbars",int(config['params_section']['red H1']))
    cv2.setTrackbarPos("red S1","trackbars",int(config['params_section']['red S1']))
    cv2.setTrackbarPos("red V1","trackbars",int(config['params_section']['red V1']))
    cv2.setTrackbarPos("red H2","trackbars",int(config['params_section']['red H2']))
    cv2.setTrackbarPos("red S2","trackbars",int(config['params_section']['red S2']))
    cv2.setTrackbarPos("red V2","trackbars",int(config['params_section']['red V2']))

    cv2.setTrackbarPos("aspect ratio min","trackbars",int(config['params_section']['aspect ratio min']))
    cv2.setTrackbarPos("aspect ratio max","trackbars",int(config['params_section']['aspect ratio max']))
    cv2.setTrackbarPos("extent max","trackbars",int(config['params_section']['extent max']))

def get_trackbar_values(config):
   
    config['params_section']['blue H1'] = cv2.getTrackbarPos("blue H1","trackbars")
    config['params_section']['blue S1'] = cv2.getTrackbarPos("blue S1","trackbars")
    config['params_section']['blue V1'] = cv2.getTrackbarPos("blue V1","trackbars")
    config['params_section']['blue H2'] = cv2.getTrackbarPos("blue H2","trackbars")
    config['params_section']['blue S2'] = cv2.getTrackbarPos("blue S2","trackbars")
    config['params_section']['blue V2'] = cv2.getTrackbarPos("blue V2","trackbars")

    config['params_section']['red H1'] = cv2.getTrackbarPos("red H1","trackbars")
    config['params_section']['red S1'] = cv2.getTrackbarPos("red S1","trackbars")
    config['params_section']['red V1'] = cv2.getTrackbarPos("red V1","trackbars")
    config['params_section']['red H2'] = cv2.getTrackbarPos("red H2","trackbars")
    config['params_section']['red S2'] = cv2.getTrackbarPos("red S2","trackbars")
    config['params_section']['red V2'] = cv2.getTrackbarPos("red V2","trackbars")

    config['params_section']['aspect ratio min'] = cv2.setTrackbarPos("aspect ratio min","trackbars")
    config['params_section']['aspect ratio max'] = cv2.setTrackbarPos("aspect ratio max","trackbars")
    config['params_section']['extent max'] = cv2.setTrackbarPos("extent max","trackbars")

    return config

class PiVideoStream: # from pyimagesearch
    def __init__(self, resolution=(640, 480), framerate=40):
        # initialize the camera and stream
        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.framerate = framerate
        self.camera.brightness = 50
        self.camera.contrast = 0
        self.camera.exposure_mode = "snow"
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

def make_mask_image(color_requested,params,hsv_image):

    # read current color ranges for the specified color and convert the ranges into arrays
    if color_requested == CargoColor.BLUE:
        color1 = np.array([int(params['params_section']['blue H1']),int(params['params_section']['blue S1']),int(params['params_section']['blue V1'])])
        color2 = np.array([int(params['params_section']['blue H2']),int(params['params_section']['blue S2']),int(params['params_section']['blue V2'])])
    elif color_requested == CargoColor.RED:
        color1 = np.array([int(params['params_section']['red H1']),int(params['params_section']['red S1']),int(params['params_section']['red V1'])])
        color2 = np.array([int(params['params_section']['red H2']),int(params['params_section']['red S2']),int(params['params_section']['red V2'])])

    # identify the color by checking each pixel, keeping those match the color range
    mask = cv2.inRange(hsv_image,color1,color2)

    return mask

def find_cargo(contours,params):
    
    cargo = []

    for c in contours:

        perim = cv2.arcLength(c,True)
        #a = np.linspace(0.001, 0.10, 50) # used to determine epsilon for approxPolyDP
        # # for i in a: # used to determine epsilon for approxPolyDP
        approx = cv2.approxPolyDP(c, 0.03 * perim ,True)
        #area = cv2.contourArea(approx)
        #if ((len(approx) == 7 or len(approx) == 6) and area > min_cargo_area):
        if (len(approx) == 7 or len(approx) == 6):

            # aspect ratio should be around 1 for a circle
            x,y,w,h = cv2.boundingRect(approx)
            if (h > 0):
                aspect_ratio = w / h
            else:
                aspect_ratio = 0

            # the area of the circle contour should be some amount < area of the bounding rect of the circle contour
            area = cv2.contourArea(approx)
            if (w > 0):
                extent = area / (w * h)
            else:
                extent = 0

            if DEBUG_MODE == True:
                print("aspect ratio=%f extent=%f" % (aspect_ratio,extent))

            if ((aspect_ratio > int(params['params_section']['min aspect ratio'])/100 and aspect_ratio < int(params['params_section']['max aspect ratio'])/100 ) \
            and (extent < int(params['params_section']['max extent'])/100) ):
                (x,y),radius = cv2.minEnclosingCircle(approx)
                cargo.append((area,(x,y),radius))

    return cargo

def output_data(blue_cargo,red_cargo,max_cargo):
   
    cargo_data = ""

    return cargo_data

def draw_cargo(blue_cargo, red_cargo, max_cargo, image):

    # draw cargo for each list of blue and red up to the max_cargo limit
    # cargo entries look like this: (area, (x,y), radius), for example (120, (388,140), 80)
    # sort the cargo in reverse so we can get closest max_cargo first
    # list => (120, (388,140), 80), (80, (120,366), 10)

    blue_cargo.sort(key=itemgetter(0),reverse = True)
    
    num_cargo = 0
    if len(blue_cargo) > max_cargo:
        num_cargo = max_cargo
    else:
        num_cargo = len(blue_cargo)

    for i in range(num_cargo):
        center = (int(blue_cargo[i][1][0]),int(blue_cargo[i][1][1]))
        radius = int(blue_cargo[i][2])
        cv2.circle(image,center,radius,(0,255,0),3)

    red_cargo.sort(key=itemgetter(0),reverse = True)
    num_cargo = 0
    if len(red_cargo) > max_cargo:
        num_cargo = max_cargo
    else:
        num_cargo = len(red_cargo)

    for i in range(num_cargo):
        center = (int(red_cargo[i][1][0]),int(red_cargo[i][1][1]))
        radius = int(red_cargo[i][2])
        cv2.circle(image,center,radius,(0,255,0),3)

    return(image) 


# START

# determine debug mode depending on how the program was run
if len(sys.argv) == 2 and sys.argv[1] == "debug":
    DEBUG_MODE = True
else:
    DEBUG_MODE = False

parameters = read_params_file(PARAMETERS_FILENAME)

if DEBUG_MODE == True:

    # load the current parameters from the trackbars, otherwise, keep the parameters that were just loaded from the file

    # create window with trackbars to control the parameters
    cv2.namedWindow("trackbars")
    cv2.resizeWindow("trackbars",600,800)
    cv2.createTrackbar("red H1","trackbars",0,180,callback)
    cv2.createTrackbar("red S1","trackbars",0,255,callback)
    cv2.createTrackbar("red V1","trackbars",0,255,callback)
    cv2.createTrackbar("red H2","trackbars",0,180,callback)
    cv2.createTrackbar("red S2","trackbars",0,255,callback)
    cv2.createTrackbar("red V2","trackbars",0,255,callback)
    cv2.createTrackbar("blue H1","trackbars",0,180,callback)
    cv2.createTrackbar("blue S1","trackbars",0,255,callback)
    cv2.createTrackbar("blue V1","trackbars",0,255,callback)
    cv2.createTrackbar("blue H2","trackbars",0,180,callback)
    cv2.createTrackbar("blue S2","trackbars",0,255,callback)
    cv2.createTrackbar("blue V2","trackbars",0,255,callback)
    cv2.createTrackbar("aspect ratio min","trackbars",ASPECT_RATIO_OF_1_MIN*100,ASPECT_RATIO_OF_1_MAX*100,callback)
    cv2.createTrackbar("aspect ratio max","trackbars",ASPECT_RATIO_OF_1_MIN*100,ASPECT_RATIO_OF_1_MAX*100,callback)
    cv2.createTrackbar("extent max","trackbars",EXTENT_MIN*100,EXTENT_MAX*100,callback)

    # and load the trackbars with the parameter values from the file
    set_trackbar_values(parameters)

vs = PiVideoStream().start() # create camera object and start reading images
print ("starting stream")
time.sleep(3) # camera sensor settling time
                      
while True:
    
    blue_cargo = []
    red_cargo = []

    if DEBUG_MODE == True:
        params = get_trackbar_values(parameters)
    else:
        params = parameters

    # read an image from the camara
    image = vs.read()

    # convert the image HSV for colour checking
    hsv = cv2.cvtColor(image,cv2.COLOR_BGR2HSV)

    mask = make_mask_image(CargoColor.BLUE,params,hsv)
    contours,_ = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    #cv2.drawContours(image, contours, -1, (0,255,0), 3)
    blue_cargo = find_cargo(contours,params)
    
    mask = make_mask_image(CargoColor.RED,params,hsv)
    contours,_ = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    red_cargo = find_cargo(contours,params)

    data = output_data(blue_cargo, red_cargo, CARGO_TO_OUTPUT_MAX)
    if DEBUG_MODE == True:
        print(data)
        image = draw_cargo(blue_cargo, red_cargo, CARGO_TO_OUTPUT_MAX, image)

        # update all the images
        cv2.imshow("RPiVideo",image)
        #cv2.imshow("HSV",hsv)
        cv2.imshow("Mask",mask)

        if process_user_key() == True:
            break
        
# cleanup
cv2.destroyAllWindows()
vs.stop()