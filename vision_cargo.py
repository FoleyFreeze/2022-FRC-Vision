#!/usr/bin/python3.9
import cv2
from picamera.array import PiRGBArray
from picamera import PiCamera
from threading import Thread
import time
import numpy as np
import PySimpleGUI as sg

def callback(pos):
    pass

def read_color():
    # reading the current colour value ranges
    hue1 = cv2.getTrackbarPos("H1","window")
    sat1 = cv2.getTrackbarPos("S1","window")
    value1 = cv2.getTrackbarPos("V1","window")
    hue2 = cv2.getTrackbarPos("H2","window")
    sat2 = cv2.getTrackbarPos("S2","window")
    value2 = cv2.getTrackbarPos("V2","window")
    return(hue1, sat1, value1, hue2, sat2, value2)

def write_colors_file(file,h1,s1,v1,h2,s2,v2):
    print(file)

class PiVideoStream: # from pyimagesearch
    def __init__(self, resolution=(640, 480), framerate=40):
        # initialize the camera and stream
        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.framerate = framerate
        # self.camera.brightness = 70
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

# create window with trackbars to control the color range
cv2.namedWindow("window")
cv2.resizeWindow("window",600,800)
cv2.createTrackbar("H1","window",0,180,callback)
cv2.createTrackbar("S1","window",0,255,callback)
cv2.createTrackbar("V1","window",0,255,callback)
cv2.createTrackbar("H2","window",0,180,callback)
cv2.createTrackbar("S2","window",0,255,callback)
cv2.createTrackbar("V2","window",0,255,callback)
cv2.createTrackbar("min cargo area","window",0,100,callback)
cv2.createTrackbar("color window save","window",0,1,callback)
cv2.setTrackbarPos("color window save", "window", 0)

vs = PiVideoStream().start() # create camera object and start reading images
print ("starting stream")
time.sleep(3) # camera sensor settling time
                      
while True:
    
    # read an image from the camara
    image = vs.read()

    # convert the image HSV for colour checking
    hsv = cv2.cvtColor(image,cv2.COLOR_BGR2HSV)

    # read current color ranges
    (h1,s1,v1,h2,s2,v2) = read_color()

    min_cargo_area = cv2.getTrackbarPos("min cargo area","window")

    # convert color value ranges into array 
    color1 = np.array([h1,s1,v1])
    color2 = np.array([h2,s2,v2])
    
    # identify the color by checking the pixel
    mask = cv2.inRange(hsv,color1,color2)
    
    contours,_ = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    #cv2.drawContours(image, contours, -1, (0,255,0), 3)

    for c in contours:
        perim = cv2.arcLength(c,True)
        approx = cv2.approxPolyDP(c,0.02,True)
        area = cv2.contourArea(c)
        if (len(approx) > 5 and area > min_cargo_area):
            (x,y),radius = cv2.minEnclosingCircle(c)
            center = (int(x),int(y))
            radius = int(radius)
            cv2.circle(image,center,radius,(0,255,0),3)
    
    # update all the images
    cv2.imshow("RPiVideo",image)
    cv2.imshow("HSV",hsv)
    cv2.imshow("Mask",mask)

    save_colors =  cv2.getTrackbarPos("color window save","window")
    if save_colors == 1:
        values_file = sg.popup_get_file("color values file")
        if not values_file:
            values_file = "default"
        write_colors_file(values_file,h1,s1,v1,h2,s2,v2)
    cv2.setTrackbarPos("color window save", "window", 0)

    # if Esc key is pressed exit program
    key = cv2.waitKey(1)
    if key == 27:
        break

# cleanup
cv2.destroyAllWindows()
vs.stop()

