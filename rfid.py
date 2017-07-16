#!/usr/bin/env python

#Basic imports
from ctypes import *
import os
import signal
import subprocess
import sys
import time
import datetime
import urllib2
import urllib
import signal
import math
import termios

#Phidget specific imports
from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException
from Phidgets.Events.Events import AttachEventArgs, DetachEventArgs, ErrorEventArgs, OutputChangeEventArgs, TagEventArgs
from Phidgets.Devices.RFID import RFID, RFIDTagProtocol
from Phidgets.Phidget import PhidgetLogLevel

#Home path
homepath ='/home/pi/Desktop/Sign-In Script/'

#Sound library path
audlib=homepath + 'aud/'

#Time Card log path
logpath=homepath + 'log/'

#Displayed Message file
display='/var/www/html/message.txt'

#Tag Assignment list file
tags='/var/www/html/tag.txt'


old_settings = None 
global name
global tagsList
#global tagStatus

tagsList=list()
#tagStatus=list()

#Create an RFID object
try:
    rfid = RFID()
except RuntimeError as e:
    print("Runtime Exception: %s" % e.details)
    print("Exiting....")
    exit(1)
     
tagsList=list()
#tagStatus=list()

with open(tags) as f:
    tagsList = f.read().splitlines()
                     
#for index in range(len(tagsList)):
#    tagStatus.append(0)
         
#Create an RFID object
try:
    rfid = RFID()
except RuntimeError as e:
    print("Runtime Exception: %s" % e.details)
    print("Exiting....")
    exit(1)

def actionOnAttach(e):
    #TODO  performed once when device attached
    time.sleep(5)
    playSound('charge')

def actionOnDetach(e):
    #TODO  performed once when device detached
    playSound('error')
    time.sleep(3)
    reboot()

def actionOnOutputChange(e):
    #TODO  performed once when terminal block output changes
    print("Attached")

def actionOnTagFound(e):
    #TODO  performed once when tag is in range
    t = e.tag
    if t == "Guest1":
        reboot()
    print(t)

    try:
        for idx in range(0,len(tagsList)):
	    assignee=tagsList[idx].split('=')
	    if assignee[0]==e.tag:
	        name=assignee[1]
		break
	    else:
		name='Guest_' + t
        now = datetime.datetime.now()
        time_card = logpath + name + '.log'
        timeCardExists = os.path.isfile(time_card)
        overwriteCard = not timeCardExists

        printToLog(name, now)

        if timeCardExists:
            in_count=0
            out_count=0
            times= list()
            with open(time_card) as ts:
                line = ts.read()
                in_count+=line.count("In")
                out_count+=line.count("Out")
                
            with open(time_card) as ts:
                times = ts.read().splitlines()
            
            time_line = times[len(times)-1]
            time_ary = time_line.split(",")

            print(times[len(times)-1])
            print(times[len(times)-1].count(":"))

            while(len(time_ary) < 5):
                time_ary.append("")

            for idx in range(0, 4):
                print(time_ary[idx])
            
            if times[len(times)-1].count(":") >= 4:
                time_msg = "\n{}".format( now.strftime('%m/%d/%y,%H:%M:%S,'))
                printToFile(time_card, time_msg, False)
                printToFile(display, "Welcome, " + name, True)
            else:
                time_line= times[len(times)-1]
                #time_idx= time_line.index(":")
                #idx_start = time_idx-2
                #idx_stop = time_idx+6
                #timeIn = time_line[idx_start : idx_stop]
                time_msg = "{}".format( now.strftime('%m/%d/%y,%H:%M:%S,'))
                date_time = time_msg.split(",")
                timeIn = time_ary[1]
                timeOut = date_time[1]
                #idx_start2 = time_msg.find(":")-3
                #idx_stop2 = idx_start2+9
                #timeOut = time_msg[idx_start2 : idx_stop2]
                #print("")
                #print("Time In: " + timeIn)
                #print("Time Out: " + timeOut)
                delta = getDelta(timeIn, timeOut)
                print("Time logged: " + delta)
                print(time_msg)
                printToFile(time_card, time_msg + delta + " " + calculateHours(delta), False)
                printToFile(display, "Goodbye, " + name + " (" + delta + ")", True)
        else:
            time_msg = "{}".format( now.strftime('%m/%d/%y,%H:%M:%S,'))
            printToFile(time_card, time_msg, True)
            printToFile(display, "Welcome, " + name, True)
        playSound('ding')
    except ValueError:
        print("Error unknown tag %s" % (t))

def reboot():
    command = "/usr/bin/sudo /sbin/shutdown -r now"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    print output
    
       
def playSound(snd_file):
    snd_file = audlib + snd_file + '.mp3'
    snd = subprocess.Popen(['omxplayer', '-o', 'hdmi', snd_file])
    time.sleep(1)
    snd.communicate('q')

def printToScreen(text):
    printToFile(display, text, True)

def actionOnTagLost(e):
    #TODO  performed once when tag is out of range
    time.sleep(1)

def getDelta(in_time, out_time):
    t1 = in_time.split(":")
    t2 = out_time.split(":")
    h1 = int(t1[0])
    h2 = int(t2[0])
    m1 = int(t1[1])
    m2 = int(t2[1])
    s1 = int(t1[2])
    s2 = int(t2[2])

    print(in_time)
    print(out_time)
    total = (3600*h2 + 60*m2 + s2) - (3600*h1 + 60*m1 + s1)
    h = int(math.floor(total/3600))
    total= total-(h*3600)
    m = int(math.floor(total/60))
    total = total - (m*60)
    s = int(total)
    
    if (h)<10:
        h = "0" + str(h)
    else:
        h = str(h)
    if (m)<10:
        m = "0" + str(m)
    else:
        m = str(m)
    if (s)<10:
        s = "0" + str(s)
    else:
        s = str(s)
    
    return(h+":"+m+":"+s)

def calculateHours(time):
    t = time.split(":")
    h = float(t[0])
    m = float(t[1])
    s = float(t[2])
    
    hours = (h*3600 + m*60 + s) /3600
    str_h = str(hours)
    str_h = str_h[0:4]
    
    return(str_h)

    
def printToLog(name, time):
    time_msg = name + " , {};".format(time.strftime('%m/%d/%y %H:%M:%S'))
    printToFile('/home/pi/Desktop/Sign-In Script/log/log.log', time_msg, False)


def printToFile(filename, text, overwrite):
    try:
        if overwrite:
            file = open(filename, "w+")
            file.seek(0)
	    file.truncate()
	    file.write(text)
	    file.close
        else:
            file = open(filename, "a")
            file.write(text)
	    file.close
    except ValueError:
        print("Error unknown tag %s" % (e.tag))

#
# Boilerplate formats and actions
#
         
#Information Display Function
def displayDeviceInfo():
    print("|------------|----------------------------------|--------------|------------|")
    print("|- Attached -|-              Type              -|- Serial No. -|-  Version -|")
    print("|------------|----------------------------------|--------------|------------|")
    print("|- %8s -|- %30s -|- %10d -|- %8d -|" % (rfid.isAttached(), rfid.getDeviceName(), rfid.getSerialNum(), rfid.getDeviceVersion()))
    print("|------------|----------------------------------|--------------|------------|")
    print("Number of outputs: %i -- Antenna Status: %s -- Onboard LED Status: %s" % (rfid.getOutputCount(), rfid.getAntennaOn(), rfid.getLEDOn()))
         
#Event Handler Callback Functions
def rfidAttached(e):
    attached = e.device
    actionOnAttach(e)
    print("RFID %i Attached!" % (attached.getSerialNum()))
         
def rfidDetached(e):
    detached = e.device
    actionOnDetach(e)
    print("RFID %i Detached!" % (detached.getSerialNum()))
         
def rfidError(e):
    try:
        source = e.device
        print("RFID %i: Phidget Error %i: %s" % (source.getSerialNum(), e.eCode, e.description))
    except PhidgetException as e:
        print("Phidget Exception %i: %s" % (e.code, e.details))
         
def rfidOutputChanged(e):
    #source = e.device
    #actionOnOutputChange(e)
    #print("RFID %i: Output %i State: %s" % (source.getSerialNum(), e.index, e.state))
    print("")
    
def rfidTagGained(e):
    source = e.device
    rfid.setLEDOn(1)
    actionOnTagFound(e)
    
         
def rfidTagLost(e):
    source = e.device
    rfid.setLEDOn(0)
    actionOnTagLost(e)

def init_anykey():
    global old_settings
    old_settings = termios.tcgetattr(sys.stdin)
    new_settings = termios.tcgetattr(sys.stdin)
    new_settings[3] = new_settings[3] & ~(termios.ECHO | termios.ICANON)
    new_settings[6][termios.VMIN] = 0
    new_settings[6][termios.VTIME] = 0
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, new_settings)


def term_anykey():
    global old_settings
    if old_Settings:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


def getKey():
    ch_set = []
    ch = os.read(sys.stdin.fileno(), 1)
    while ch != None and len(ch) > 0:
        ch_set.append( ord(ch[0]))
        ch = os.read(sys.stdin.fileno(), 1)
        return ch_set

def openDevice():
    try:
        rfid.openPhidget()
    except PhidgetException as e:
    	print("Phidget Exception %i: %s" % (e.code, e.details))
    	print("Exiting....")
    	exit(1)
            
#Main Program Code
try:
    #rfid.enableLogging(PhidgetLogLevel.PHIDGET_LOG_VERBOSE, "phidgetlog.log")
    rfid.setOnAttachHandler(rfidAttached)
    rfid.setOnDetachHandler(rfidDetached)
    rfid.setOnErrorhandler(rfidError)
    #rfid.setOnOutputChangeHandler(rfidOutputChanged)
    rfid.setOnTagHandler(rfidTagGained)
    rfid.setOnTagLostHandler(rfidTagLost)
except PhidgetException as e:
    print("Phidget Exception %i: %s" % (e.code, e.details))
    print("Exiting....")
    exit(1)
         
print("Opening phidget object....")
openDevice()
         
print("Waiting for attach....")

try:
    rfid.waitForAttach(10000)
except PhidgetException as e:
    print("Phidget Exception %i: %s" % (e.code, e.details))
    try:
        rfid.closePhidget()
    except PhidgetException as e:
        print("Phidget Exception %i: %s" % (e.code, e.details))
        print("Exiting....")
        exit(1)
#else:
#    displayDeviceInfo()

print("Turning on the RFID antenna....")
time.sleep(0.25)
rfid.setAntennaOn(False)
time.sleep(0.25)
rfid.setAntennaOn(True)
         
print("Press Enter to quit....")

init_anykey()
count = 0
while True:
    if count >= 10:
        count = 0
    else:
        count = count+1
    print(count)    
    key = getKey()
    if key != None:
        print key
    else:
        time.sleep(1)
                 
try:
    lastTag = rfid.getLastTag()
    print("Last Tag: %s" % (lastTag))
except PhidgetException as e:
    print("Phidget Exception %i: %s" % (e.code, e.details))
    printToFile(display, "", True)     
print("Closing...")
         
try:
    rfid.closePhidget()
except PhidgetException as e:
    print("Phidget Exception %i: %s" % (e.code, e.details))
    print("Exiting....")
    exit(1)
         
print("Done.")
exit(0)
