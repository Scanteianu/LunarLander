import tkinter as tk
import threading
import time
import math
from PIL import Image, ImageTk


# global lander width and height, and canvas width and height are in pixels
global landerImg
global landerWidth
global landerHeight
global canvasWidth
global canvasHeight
global pixelsPerMeter
global landerControls

class LanderProperties:
    def __init__(self):
        self.burnrate = 8
        self.landingSpeed=2
        self.rollRate=180 #comparable to a fighter jet which ranges from 120 to 360
        # fuel and mass similar to descent stage
        # https://en.wikipedia.org/wiki/Apollo_Lunar_Module
        # mass gets ascent gross mass added to it for the 4700
        # todo: fuel burn affects mass
        # landing speed is 2 m/s https://en.wikipedia.org/wiki/Hard_landing
        # should probably have about 2k lbs of fuel or about 1 ton https://en.wikipedia.org/wiki/Hard_landing#:~:text=Landing%20is%20the%20final%20phase,classed%20by%20crew%20as%20hard.
        # this is because apollo 11 landed with about 1k lbs aka 500kg and 45 sec left
        # estimated burn rate - 770 lbs in 45 sec is about 1k per min, round down to 900
        # 900 per min is about 15 per second, which is about 8 kg
        self.thrust = 45000 #https://en.wikipedia.org/wiki/Descent_propulsion_system
class LanderStatus:
    # all fields in this class are in SI units
    # meters, seconds, and degrees (not radians) are used
    def __init__(self):
        self.reset(0)
    def reset(self, xvelocity):
        self.xposition=0
        self.yposition=0
        self.xvelocity=xvelocity
        self.yvelocity=0
        self.angle=0
        self.drymass=2000+4700
        self.fuelmass=8000

    def updatePosition(self):
        self.xposition+=self.xvelocity
        self.yposition+=self.yvelocity
    def getMass():
        return self.drymass+self.fuelmass
class LanderControls:
    def __init__(self):
        # thrust will be proportional to percent of 100
        # roll will be in degrees, degrees per second, or degrees per second squared
        # assume roll is controlled in airbus-like manner
        self.lock=threading.Lock()
        self.thrust=0
        self.targetAngle=0

        # https://www.businessinsider.com/watch-a-360-roll-in-one-of-the-worlds-most-advanced-jet-trainers-2015-5

class PhysicsSim:
    # physics constants like  gravity
    def __init__(self):
        self.gravity=1.62
    #
    def updateLanderStatusDueToControls(self,landerProperties, landerStatus, landerControls, timeDelta):
        #update angle

        #update vertical speed
        #negative is slowing down
        # force is mass times acceleration
        #acceleration is therefore force/mass
        #force =
        landerStatus.yvelocity-=(landerProperties.maxthrust*landerControls.thrust*math.cos(math.radians(landerStatus.angle)))/landerStatus.getMass()

        #updateFuelMass
        landerStatus.fuelmass -= timeDelta*landerProperties.burnrate

    def updateLanderStatusDueToPhysics(self,landerProperties, landerStatus, timeDelta):
        #update lander's accel
        landerStatus.yvelocity+=self.gravity*timeDelta



def setUpScreen():
    global canvasWidth
    global canvasHeight
    global landerImg
    window = tk.Tk()
    canvas = tk.Canvas(window,width=canvasWidth, height=canvasHeight,bg='white')
    canvas.pack()
    landerImg= Image.open("smallLander.png")
    print(landerImg)
    landerImg.show()
    xposition = 0
    yposition = 0
    return window, canvas
def checkLanderInBounds(landerStatus):
    global landerWidth
    global landerHeight
    global canvasWidth
    global canvasHeight
    global pixelsPerMeter
    return landerStatus.xposition*pixelsPerMeter<canvasWidth-landerWidth and \
     landerStatus.yposition*pixelsPerMeter<=canvasHeight-landerHeight
def checkFuel(landerStatus):
    return landerStatus.fuelmass>0
def checkSafeLanding(landerStatus, landerProperties):
        global landerWidth
        global landerHeight
        global canvasWidth
        global canvasHeight
        global pixelsPerMeter
        return landerStatus.xposition*pixelsPerMeter>canvasWidth-landerWidth and \
            landerStatus.xposition>0 and \
            landerStatus.yposition*pixelsPerMeter<=canvasHeight-landerHeight and \
            math.abs(landerStatus.angle)<20 and \
            landerStatus.xvelocity < landerProperties.landingSpeed and \
            landerStatus.yvelocity < landerProperties.landingSpeed
def moveLander(landerStatus,landerImg, canvas):
    tklander=ImageTk.PhotoImage(landerImg.rotate(landerStatus.angle))
    lander = canvas.create_image(landerStatus.xposition*pixelsPerMeter, \
        landerStatus.yposition*pixelsPerMeter, \
        anchor=tk.NW, \
        image=tklander)
    landerProperties = LanderProperties()
    physicsSim = PhysicsSim()
    readTime=time.time()

    while True:
        oldAngle = landerStatus.angle
        time.sleep(.05)
        oldTime=readTime
        readTime=time.time()
        timeDelta=readTime-oldTime
        physicsSim.updateLanderStatusDueToPhysics(landerProperties, landerStatus, timeDelta)

        #print("move lander: "+str(landerStatus.xposition))
        landerStatus.updatePosition()
        if not (checkLanderInBounds(landerStatus) and checkFuel(landerStatus)):
            if checkSafeLanding(landerStatus, landerProperties):
                print('safe landing')
            else:
                print('unsafe landing')
            print(landerStatus.yvelocity)
            landerStatus.reset(0)

            landerStatus.angle=oldAngle+10
        if landerStatus.angle != oldAngle:
            canvas.delete(lander)
            tklander=ImageTk.PhotoImage(landerImg.rotate(landerStatus.angle))
            lander = canvas.create_image(landerStatus.xposition*pixelsPerMeter, \
                landerStatus.yposition*pixelsPerMeter, \
                anchor=tk.NW, \
                image=tklander)
        else:
            canvas.moveto(lander,landerStatus.xposition*pixelsPerMeter, \
                landerStatus.yposition*pixelsPerMeter)

        #canvas.delete(lander)
canvasWidth=600
canvasHeight=900
landerWidth=109
landerHeight=140
pixelsPerMeter=1.0
window, canvas = setUpScreen()
landerStatus = LanderStatus()
moveThread = threading.Thread(target=moveLander,args=[landerStatus,landerImg, canvas])
moveThread.start()
window.mainloop()
