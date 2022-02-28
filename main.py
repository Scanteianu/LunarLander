import tkinter as tk
import threading
import time
from PIL import Image, ImageTk

global landerImg

class LanderStatus:
    def __init__(self):
        self.lock=threading.Lock()
        self.reset(1)
    def reset(self, xvelocity):
        self.xposition=0
        self.yposition=0
        self.xvelocity=xvelocity
        self.yvelocity=0
        self.angle=0
    def updatePosition(self):
        self.xposition+=self.xvelocity
        self.yposition+=self.yvelocity



def setUpScreen():
    global landerImg
    window = tk.Tk()
    canvas = tk.Canvas(window,width=600, height=900,bg='white')
    canvas.pack()
    landerImg= Image.open("smallLander.png")
    print(landerImg)
    landerImg.show()
    xposition = 0
    yposition = 0
    return window, canvas
def checkLanderInBounds(landerStatus):
    return landerStatus.xposition<600 and landerStatus.yposition<900
def moveLander(landerStatus,landerImg, canvas):
    tklander=ImageTk.PhotoImage(landerImg.rotate(landerStatus.angle))
    lander = canvas.create_image(landerStatus.xposition, \
        landerStatus.yposition, \
        anchor=tk.NW, \
        image=tklander)

    while True:
        oldAngle = landerStatus.angle
        time.sleep(.05)

        print("move lander: "+str(landerStatus.xposition))
        landerStatus.updatePosition()
        if not checkLanderInBounds(landerStatus):
            landerStatus.reset(1)
            landerStatus.angle+=10
        if landerStatus.angle != oldAngle:
            canvas.delete(lander)
            tklander=ImageTk.PhotoImage(landerImg.rotate(landerStatus.angle))
            lander = canvas.create_image(landerStatus.xposition, \
                landerStatus.yposition, \
                anchor=tk.NW, \
                image=tklander)
        else:
            canvas.moveto(lander,landerStatus.xposition,landerStatus.yposition)

        #canvas.delete(lander)

window, canvas = setUpScreen()
landerStatus = LanderStatus()
moveThread = threading.Thread(target=moveLander,args=[landerStatus,landerImg, canvas])
moveThread.start()
window.mainloop()
