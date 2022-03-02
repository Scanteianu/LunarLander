import tkinter as tk
import tkinter.ttk as ttk
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
        self.maxthrust = 45000 #https://en.wikipedia.org/wiki/Descent_propulsion_system
class LanderStatus:
    # all fields in this class are in SI units
    # meters, seconds, and degrees (not radians) are used
    def __init__(self):
        self.reset(0)
    def reset(self, xvelocity):
        self.xposition=0
        self.yposition=0
        self.xvelocity=xvelocity
        self.yvelocity=15 #https://space.stackexchange.com/questions/40902/apollo-altitude-vs-rate-of-descent-schedule
        #36fps == 10 mps at 1k ft, 30 mps at 3k ft, so at 450m, which is 1.5*300m, 15 mps
        self.angle=0
        #drymass is ascent total mass plus descent phase mass minus descent phase fuel (2000)
        self.drymass=2000+4700
        self.fuelmass=2000
        self.startingfuelmass=2000

    def getMass(self):
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
        landerStatus.yvelocity-=((landerProperties.maxthrust*landerControls.thrust*math.cos(math.radians(landerStatus.angle)))/landerStatus.getMass())*timeDelta

        #updateFuelMass
        landerStatus.fuelmass -= timeDelta*landerProperties.burnrate

    def updateLanderStatusDueToPhysics(self,landerProperties, landerStatus, timeDelta):
        #update lander's accel
        landerStatus.yvelocity+=self.gravity*timeDelta
        landerStatus.xposition+=landerStatus.xvelocity*timeDelta
        landerStatus.yposition+=landerStatus.yvelocity*timeDelta


def throttleUp(event):
    global landerControls
    landerControls.lock.acquire()
    if landerControls.thrust <1.0:
        landerControls.thrust+=0.05
    landerControls.lock.release()
def throttleDown(event):
    global landerControls
    landerControls.lock.acquire()
    if landerControls.thrust >0.0:
        landerControls.thrust-=0.05
    landerControls.lock.release()
def setUpScreen():
    global canvasWidth
    global canvasHeight
    global landerImg
    window = tk.Tk()
    canvas = tk.Canvas(window,width=canvasWidth, height=canvasHeight,bg='white')
    canvas.grid(row=0,column=0)

    throttleLabel= tk.Label(window, text="throttle")
    throttleLabel.grid(row=1,column=0)

    throttle = ttk.Progressbar(window, orient = tk.HORIZONTAL,
              length = 100, mode = 'determinate')
    throttle.grid(row=1,column=1)

    infoLabel = tk.Label(window,text="")
    infoLabel.grid(row=2,column=0)
    landerImg= Image.open("smallLander.png")
    print(landerImg)
    #landerImg.show()
    window.bind('<Up>', throttleUp)
    window.bind('<Down>', throttleDown)
    xposition = 0
    yposition = 0
    return window, canvas, throttle, infoLabel
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
        return landerStatus.xposition*pixelsPerMeter<=canvasWidth-landerWidth and \
            landerStatus.xposition>=0 and \
            landerStatus.yposition*pixelsPerMeter<=canvasHeight-landerHeight and \
            math.abs(landerStatus.angle)<20 and \
            landerStatus.xvelocity < landerProperties.landingSpeed and \
            landerStatus.yvelocity < landerProperties.landingSpeed
def moveLander(landerStatus,landerImg, canvas, throttle, infoLabel):
    global landerControls
    global canvasHeight
    global pixelsPerMeter
    global landerHeight
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
        landerControls.lock.acquire()
        throttle['value']=landerControls.thrust*100
        landerControls.lock.release()
        oldTime=readTime
        readTime=time.time()
        timeDelta=readTime-oldTime
        physicsSim.updateLanderStatusDueToPhysics(landerProperties, landerStatus, timeDelta)
        physicsSim.updateLanderStatusDueToControls(landerProperties, landerStatus, landerControls, timeDelta)

        infoString = 'Vertical Speed: {0: .2f} Fuel: {1: .2f} Altitude: {2: .2f} '.format(landerStatus.yvelocity, landerStatus.fuelmass, ((canvasHeight-landerHeight)-landerStatus.yposition/pixelsPerMeter)*pixelsPerMeter)
        #print("move lander: "+str(landerStatus.xposition))
        infoLabel.config(text=infoString)
        if not (checkLanderInBounds(landerStatus) and checkFuel(landerStatus)):
            if checkSafeLanding(landerStatus, landerProperties):
                print('safe landing')
                infoLabel.config(text=infoString + " => safe landing")
                time.sleep(5)
            else:
                print('unsafe landing')
                infoLabel.config(text=infoString+" => unsafe landing")
                time.sleep(5)
            print(landerStatus.yvelocity)
            landerStatus.reset(0)
            readTime=time.time()

            #landerStatus.angle=oldAngle+10
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
pixelsPerMeter=2.0
landerStatus = LanderStatus()
landerControls = LanderControls()
window, canvas, throttle, infoLabel = setUpScreen()
moveThread = threading.Thread(target=moveLander,args=[landerStatus,landerImg, canvas, throttle, infoLabel])
moveThread.start()
window.mainloop()
