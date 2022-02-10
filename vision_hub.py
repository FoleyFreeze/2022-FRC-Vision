#!/usr/bin/python3.9
import cv2
from picamera.array import PiRGBArray
from picamera import PiCamera
from threading import Thread
import time
import numpy as np
import PySimpleGUI as sg
import configparser

DEFAULT_PARAMETERS_FILENAME = "default-params.ini"
PARAMETERS_FILENAME = "Latest working params"

def callback(pos):
    pass


def read_color():
    # reading the current colour value ranges
    hue1 = cv2.getTrackbarPos("H1","trackbars")
    sat1 = cv2.getTrackbarPos("S1","trackbars")
    value1 = cv2.getTrackbarPos("V1","trackbars")
    hue2 = cv2.getTrackbarPos("H2","trackbars")
    sat2 = cv2.getTrackbarPos("S2","trackbars")
    value2 = cv2.getTrackbarPos("V2","trackbars")
    return(hue1, sat1, value1, hue2, sat2, value2)

# for writing parameters file to be used upon next run
def write_params_file(file):
    print("Writing parameter file " + file)
    config = configparser.ConfigParser()
    config.add_section('params_section')
    config['params_section']['H1'] = str(cv2.getTrackbarPos("H1","trackbars"))
    config['params_section']['S1'] = str(cv2.getTrackbarPos("S1","trackbars"))
    config['params_section']['V1'] = str(cv2.getTrackbarPos("V1","trackbars"))
    config['params_section']['H2'] = str(cv2.getTrackbarPos("H2","trackbars"))
    config['params_section']['S2'] = str(cv2.getTrackbarPos("S2","trackbars"))
    config['params_section']['V2'] = str(cv2.getTrackbarPos("V2","trackbars"))
    config['params_section']['min cargo area'] = str(cv2.getTrackbarPos("min cargo area","trackbars"))
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
    
    hue1 = config['params_section']['H1']
    cv2.setTrackbarPos("H1","trackbars",int(hue1))
    sat1 = config['params_section']['S1']
    cv2.setTrackbarPos("S1","trackbars",int(sat1))
    value1 = config['params_section']['V1']
    cv2.setTrackbarPos("V1","trackbars",int(value1))
    hue2 = config['params_section']['H2']
    cv2.setTrackbarPos("H2","trackbars",int(hue2))
    sat2 = config['params_section']['S2']
    cv2.setTrackbarPos("S2","trackbars",int(sat2))
    value2 = config['params_section']['V2']
    cv2.setTrackbarPos("V2","trackbars",int(value2))
    area = config['params_section']['min cargo area']
    cv2.setTrackbarPos("min cargo area","trackbars",int(area))

class PiVideoStream: # from pyimagesearch
    def __init__(self, resolution=(800, 600), framerate=40, brightness=54, \
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

def show_x_and_y(event, x, y, flags, userdata):
    if event == cv2.EVENT_LBUTTONDOWN:
        print('({x},{y})'.format(x=x,y=y))

# START

# create window with trackbars to control the color range
cv2.namedWindow("trackbars")
cv2.resizeWindow("trackbars",600,800)
cv2.createTrackbar("H1","trackbars",0,180,callback)
cv2.createTrackbar("S1","trackbars",0,255,callback)
cv2.createTrackbar("V1","trackbars",0,255,callback)
cv2.createTrackbar("H2","trackbars",0,180,callback)
cv2.createTrackbar("S2","trackbars",0,255,callback)
cv2.createTrackbar("V2","trackbars",0,255,callback)
cv2.createTrackbar("min cargo area","trackbars",0,500,callback)

read_params_file(PARAMETERS_FILENAME)

vs = PiVideoStream().start() # create camera object and start reading images
print ("starting stream")
time.sleep(3) # camera sensor settling time

callback_set = False

while True:
    
    # read an image from the camara
    image = vs.read()

    # convert the image HSV for colour checking
    hsv = cv2.cvtColor(image,cv2.COLOR_BGR2HSV)

    # read current color ranges
    (h1,s1,v1,h2,s2,v2) = read_color()

    #min_cargo_area = cv2.getTrackbarPos("min cargo area","trackbars")

    # convert color value ranges into array 
    color1 = np.array([h1,s1,v1])
    color2 = np.array([h2,s2,v2])  
    # identify the color by checking the pixel
    mask = cv2.inRange(hsv,color1,color2)

    '''contours,_ = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    #cv2.drawContours(image, contours, -1, (0,255,0), 3)

    for c in contours:
        perim = cv2.arcLength(c,True)
        #a = np.linspace(0.001, 0.10, 50)
        # # for i in a:
        approx = cv2.approxPolyDP(c, 0.03 * perim ,True)
        #area = cv2.contourArea(approx)
        #if ((len(approx) == 7 or len(approx) == 6) and area > min_cargo_area):
        if (len(approx) == 7 or len(approx) == 6):
            (x,y),radius = cv2.minEnclosingCircle(approx)
            center = (int(x),int(y))
            radius = int(radius)
            cv2.circle(image,center,radius,(0,255,0),3)
            #for debugging min area
            #_ = cv2.putText(image, str(area), center, cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255) , 3 , cv2.LINE_AA)
            #for debugging number of vertices
            #_ = cv2.putText(image, str(len(approx)), center, cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255) , 3 , cv2.LINE_AA)
                #print(i)
                #print(len(approx))'''

    # update all the images
    cv2.imshow("RPiVideo",image)
    #cv2.imshow("HSV",hsv)
    cv2.imshow("Mask",mask)

    if(callback_set == False):
        cv2.setMouseCallback("RPiVideo", show_x_and_y)
        callback_set = True

    if process_user_key() == True:
        break
        

# cleanup
cv2.destroyAllWindows()
vs.stop()

