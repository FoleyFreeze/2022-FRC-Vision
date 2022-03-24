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
PARAMETERS_FILENAME = "cargo_fieldhouse_red_blue_gamma_200_lights"
ASPECT_RATIO_OF_1_MIN = 90
ASPECT_RATIO_OF_1_MAX = 140
EXTENT_MIN = 70
EXTENT_MAX = 85
CARGO_TO_OUTPUT_MAX = 1
HORIZONTAL_FOV = 90
GAMMA_MIN = 30
GAMMA_MAX = 200
GAMMA_CURRENT = 200 # 100 is no correction; 0 < gamma < 100 => darker image; gamma > 100 => brighter image
GAMMA_ENABLE = True
CARGO_MAX = 22 # limit the total number of cargo recognized
# From refernce drawing:
# https://www.uctronics.com/arducam-90-degree-wide-angle-1-2-3-m12-mount-with-lens-adapter-for-raspberry-pi-high-quality-camera.html
# arctan (4.92/2) /3.28 = 36.86989765, for half the verical
# then 2x for the full veritcal => 36.86989765 * 2 = 73.7397953 => 74 
VERTICAL_FOV = 74
PIXEL_WIDTH = 640
PIXEL_HEIGHT = 480
HORIZONTAL_PIXEL_CENTER = (PIXEL_WIDTH / 2) - 0.5
VERTICAL_PIXEL_CENTER = (PIXEL_HEIGHT / 2) - 0.5 
HORIZONTAL_DEGREES_PER_PIXEL  = HORIZONTAL_FOV / PIXEL_WIDTH 
VERTICAL_DEGREES_PER_PIXEL = VERTICAL_FOV / PIXEL_HEIGHT
AREA_MIN = 200
OUTPUT_MODE = False
DEBUG_MODE = False
ANGLE_INCREMENT = 12
X_PIXEL_ADJUSTMENT = 0
Y_PIXEL_ADJUSTMENT = 0    

class CargoColor(Enum):
    BLUE = 1
    RED = 2

class CargoCameraType(Enum):
    LEFT = 0
    RIGHT = 1

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
    config['params_section']['gamma'] = str(cv2.getTrackbarPos("gamma","trackbars"))
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
    cv2.setTrackbarPos("gamma","trackbars",int(config['params_section']['gamma']))

def get_trackbar_values(config):
   
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
    config['params_section']['gamma'] = str(cv2.getTrackbarPos("gamma","trackbars"))

    return config

class PiVideoStream: # from pyimagesearch
    def __init__(self, resolution=(PIXEL_WIDTH, PIXEL_HEIGHT), framerate=40):
        # initialize the camera and stream
        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.framerate = framerate
        #self.camera.brightness = 50
        #self.camera.contrast = 0
        #self.camera.exposure_mode = "snow"
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
    else:
        #if something really wrong, kill program
        sys.exit("make_mask_image: invalid color")

    # identify the color by checking each pixel, keeping those match the color range
    mask = cv2.inRange(hsv_image,color1,color2)

    return mask

def find_cargo(contours,params):
    
    cargo = []

    #print("len contours=%d" % (len(contours)))

    for c in contours:

        perim = cv2.arcLength(c,True)
        approx = cv2.approxPolyDP(c, 0.02 * perim ,True)
        area = cv2.contourArea(approx)

        #print("len approx=%d" % (len(approx)))
        #if (len(approx) >= 7 and len(approx) <= 9) and area > AREA_MIN:
        if (len(approx) > 4) and area > AREA_MIN:

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

            (x,y),radius = cv2.minEnclosingCircle(approx)
            area_min_circle = math.pi * (radius * radius)
            area_ratio = area / area_min_circle
            
            #if DEBUG_MODE == True:
            #   print("before aspect=%f,a=%f,ex=%f,ratio=%f" % (aspect_ratio,area,extent,area_ratio))

            if (area_ratio > 0.8):
                        
                if ((aspect_ratio >= ASPECT_RATIO_OF_1_MIN/100 and aspect_ratio <= ASPECT_RATIO_OF_1_MAX/100 )):
                        #if DEBUG_MODE == True:
                        #   print("after aspect=%f,a=%f,ex=%f,ratio=%f" % (aspect_ratio,area,extent,area_ratio))

                        (x,y),radius = cv2.minEnclosingCircle(approx)
                        x_adjusted = x + X_PIXEL_ADJUSTMENT
                        y_adjusted = y + Y_PIXEL_ADJUSTMENT
                        cargo.append((area,(x_adjusted,y_adjusted),radius))

    return cargo

def output_data(loops, current_time, calc_time, blue_cargo, red_cargo, max_cargo):

    blue_cargo.sort(key=itemgetter(0),reverse = True)
    
    num_cargo = 0
    if len(blue_cargo) > max_cargo:
        num_cargo = max_cargo
    else:
        num_cargo = len(blue_cargo)

    for i in range(num_cargo):
        cam_distance = look_up_distance_y(blue_cargo[i][1][1]) # blue_cargo[i][1][1] is the y-pixel at this point in the list
        #print("by=%d" % (blue_cargo[i][1][1]))

        cam_angle_of_horizontal = calc_horizontal_angle_of(blue_cargo[i][1][0]) # blue_cargo[i][1][0] is the x-pixel at this point in the list

        cargo_data = "%d,%8.3f,%8.3f,%8.3f,%8.3f,%d,%d" % (loops,current_time,calc_time,cam_distance,cam_angle_of_horizontal,CargoColor.BLUE.value,camera_location)

        nt.putString("Cargo",cargo_data)
        if DEBUG_MODE == True:
            print(cargo_data)
       
        loops = loops + 1
    #print("len(red_cargo)=%d" % (len(red_cargo)))

    red_cargo.sort(key=itemgetter(0),reverse = True)    
    num_cargo = 0
    if len(red_cargo) > max_cargo:
        num_cargo = max_cargo
    else:
        num_cargo = len(red_cargo)

    for i in range(num_cargo):
        cam_distance = look_up_distance_y(red_cargo[i][1][1]) # red_cargo[i][1][1] is the y-pixel at this point in the list
        #print("ry=%d" % (red_cargo[i][1][1]))
        cam_angle_of_horizontal = calc_horizontal_angle_of(red_cargo[i][1][0]) # red_cargo[i][1][0] is the x-pixel at this point in the list

        cargo_data = "%d,%8.3f,%8.3f,%8.3f,%8.3f,%d,%d" % (loops,current_time,calc_time,cam_distance,cam_angle_of_horizontal,CargoColor.RED.value,camera_location)

        nt.putString("Cargo",cargo_data)
       
        if DEBUG_MODE == True:
            print(cargo_data)

        loops = loops + 1

    return loops

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

def calc_horizontal_angle_of(x_pixel):
    return (x_pixel - HORIZONTAL_PIXEL_CENTER) * HORIZONTAL_DEGREES_PER_PIXEL

def look_up_distance_y(y_pixel):
    return (regress(y_pixel))

def make_color_LUT(params):
    #gamma = (int(params['params_section']['gamma']))
    gamma_converted = GAMMA_CURRENT / 100
    inverse_gamma = 1.0 / gamma_converted
    values = np.arange(0,256,dtype = np.uint8)
    for v in values:
        values[v] = ((v / 255.0) ** inverse_gamma) * 255
    return values

def find_point_on_bounding_circle(x,y,r,theta):
    x_circle = r * math.cos(math.radians(theta))
    y_circle = r * math.sin(math.radians(theta))
    return x_circle, y_circle

def make_list_of_circle_points(x,y,r):

    points = []

    for theta in 360:
        x_point, y_point = find_point_on_bounding_circle(x,y,r,theta)
        points.append((x_point,y_point))
        theta = theta + 360 / ANGLE_INCREMENT
    return points

def find_contour_points_on_bounding_circle(x,y,r,contour):
    
    bounding_circle_points = make_list_of_circle_points(x,y,r)

# y pixel and distance data that made cargo_terms and is used by regress
#367,6
#300,12
#280,18
#242,24
#218,30
#197,36
#171,48
#152,60
#143,72
#136,84
#129,96
#125,108
#123,120
#119,132
#115,144

cargo_terms = [
     2.5348515514866349e+003,
    -5.0944933066340255e+001,
     4.1457301321061552e-001,
    -1.6714838482358727e-003,
     3.3161347183020954e-006,
    -2.5843521779150704e-009
]

def regress(x):
  t = 1
  r = 0
  for c in cargo_terms:
    r += c * t
    t *= x
  return r

# START

loops = 0

camera_location = None

# determine debug mode depending on how the program was run
if len(sys.argv) == 3:

    if sys.argv[1] == "debug":
        DEBUG_MODE = True
    else:
        DEBUG_MODE = False

    if sys.argv[2] == "output":
        OUTPUT_MODE = True
    else:
        OUTPUT_MODE = False

GPIO.setmode(GPIO.BOARD)
GPIO.setup(8, GPIO.IN)
if GPIO.input(8):
    camera_location = CargoCameraType.LEFT.value
    print("Pin 8 is HIGH-LEFT CAMERA")
else:
    camera_location = CargoCameraType.RIGHT.value
    print("Pin 8 is LOW-RIGHT CAMERA")


NetworkTables.initialize(RIO_IP)
NetworkTables.setUpdateRate(0.010)
nt = NetworkTables.getTable("pi")

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
    cv2.createTrackbar("aspect ratio min","trackbars",ASPECT_RATIO_OF_1_MIN,ASPECT_RATIO_OF_1_MAX,callback)
    cv2.createTrackbar("aspect ratio max","trackbars",ASPECT_RATIO_OF_1_MIN,ASPECT_RATIO_OF_1_MAX,callback)
    cv2.createTrackbar("extent max","trackbars",EXTENT_MIN,EXTENT_MAX,callback)
    cv2.createTrackbar("gamma","trackbars",GAMMA_MIN,GAMMA_MAX,callback)

    # and load the trackbars with the parameter values from the file
    set_trackbar_values(parameters)

vs = PiVideoStream().start() # create camera object and start reading images
print ("starting stream")
time.sleep(3) # camera sensor settling time

values = []

if DEBUG_MODE == False and GAMMA_ENABLE == True:
    values = make_color_LUT(parameters)
    
while True:

    # start with robot time then add processing time at the end
    start_time_robot = nt.getNumber("RobotTime",0)
    start_time_pi = time.process_time()

    nt.putNumber("PiTime",start_time_pi)

    blue_cargo = []
    red_cargo = []

    if DEBUG_MODE == True:
        params = get_trackbar_values(parameters)
        if GAMMA_ENABLE == True and GAMMA_CURRENT != 100:
            values = make_color_LUT(params)
    else:
        params = parameters

    # read an image from the camara
    # camera is mounted upside down, so the image needs to be flipped around the x-axis
    flipped_image = vs.read()
    image = cv2.flip(flipped_image,0)
    
    if GAMMA_ENABLE == True and GAMMA_CURRENT != 100:
        #color correction
        image = cv2.LUT(image,values)
    
    # convert the image HSV for colour checking
    hsv = cv2.cvtColor(image,cv2.COLOR_BGR2HSV)

    mask_blue = make_mask_image(CargoColor.BLUE,params,hsv)
    contours,_ = cv2.findContours(mask_blue,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    #cv2.drawContours(image, contours, -1, (0,255,0), 3)
    blue_cargo = find_cargo(contours,params)
    
    mask_red = make_mask_image(CargoColor.RED,params,hsv)
    contours,_ = cv2.findContours(mask_red,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    red_cargo = find_cargo(contours,params)

    end_time_pi = time.process_time()
    calc_time = end_time_pi - start_time_pi

    loops = output_data(loops, start_time_robot, calc_time, blue_cargo, red_cargo, CARGO_TO_OUTPUT_MAX)
    if DEBUG_MODE == True:
       
        image = draw_cargo(blue_cargo, red_cargo, CARGO_TO_OUTPUT_MAX, image)

        # update all the images
        cv2.imshow("RPiVideo",image)
        #cv2.imshow("HSV",hsv)
        cv2.imshow("Mask Blue",mask_blue)
        cv2.imshow("Mask Red",mask_red)


        if process_user_key() == True:
            break
        
# cleanup
cv2.destroyAllWindows()
vs.stop()
