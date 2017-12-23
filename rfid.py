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





#USER VARIABLES
HOMEPATH = '/home/pi/Desktop/Sign-In Script/'
AUDLIB = HOMEPATH + 'aud/'
LOGPATH = HOMEPATH + 'log/'

HIDDENPATH = '/var/www/html/'
DISPLAY = HIDDENPATH + 'message.txt'
TAGS = HIDDENPATH + 'tag.txt'
COMMANDS = HIDDENPATH + 'commands.txt'
FILEFORMAT = '.odf'


global RFID
try:
    print("Opening phidget object....")
    RFID = RFID()
    RFID.openPhidget()
except RuntimeError as e:
    print("Runtime Exception: %s" % e.details)
    print("Exiting....")
    exit(1)





Old_settings = None 
global Name
global Pin
global Timecard
global TagsList
global CommandsList

TagsList=list()
with  open(TAGS) as f:
    TagsList = f.read().splitlines()

CommandsList=list()
with open(COMMANDS) as f:
    CommandsList = f.read().splitlines()






def login(Name):
    new_card = not timecardFound(Name)
    Timecard = getTimecard(Name)
    now = getTime()

    print("Psst, this person's pin is " + getPin(Name))
    if new_card:
        time_msg = "{}".format( now.strftime('%m/%d/%y,%H:%M:%S,'))
    else:
        time_msg = "\n{}".format( now.strftime('%m/%d/%y,%H:%M:%S,'))

    printToFile(Timecard, time_msg, new_card)
    printToFile(DISPLAY, "Welcome, " + Name, True)
    playSound('ding')

def logout(Name):
    Timecard = getTimecard(Name)
    now = getTime()
    with open(Timecard) as ts:
        times = ts.read().splitlines()
        time_line = times[len(times)-1]
        time_ary = time_line.split(",")
        
    time_msg = "{}".format( now.strftime('%m/%d/%y,%H:%M:%S,'))
    date_time = time_msg.split(",")
    timeIn = time_ary[1]
    timeOut = date_time[1]
    delta = getDelta(timeIn, date_time[1])
    print("Time logged: " + delta)
    print(time_msg)
    printToFile(Timecard, time_msg + delta + " " + calculateHours(delta), False)
    printToFile(DISPLAY, "Goodbye, " + Name + " (" + delta + ")", True)
    playSound('ding')

def getName(tag):
    Name = "None"
    for idx in range(0,len(TagsList)):
        assignee=TagsList[idx].split('=')
        if assignee[0]==tag:
            Name=assignee[1]
            break
        else:
            Name='Guest_' + tag
    return Name

def getPin(tag):
    Pin = "None"
    try:
        for idx in range(0,len(TagsList)):
            assignee=TagsList[idx].split('=')
            if assignee[0]==tag:
                Pin = assignee[2]
                break
    except ArrayOutOfBoundsException:
        Pin = "None"
    
    return Pin

def getNameByPin(pin):
    Name="None"
    try:
        for idx in range(0,len(TagsList)):
            assignee=TagsList[idx].split('=')
            if assignee[2]==pin:
                Name = assignee[1]
                break
    except ArrayOutOfBoundsException:
        Name = "None"
    
    return Name

def getCommand(tag):
    command = "None"
    for idx in range(0, len(CommandsList)):
        commands = CommandsList[idx].split('=')
        if commands[0]==tag:
            command = HIDDENPATH + command[1]
            break
    return command


def getTimecard(Name):
    Timecard = LOGPATH + Name + FILEFORMAT
    return Timecard

def timecardFound(Name):
    try:
        Timecard = getTimecard(Name)
        return os.path.isfile(Timecard)
    except ValueError:
        print("Error checking for timecard")

def getTime():
    return datetime.datetime.now()

def reboot():
    command = "/usr/bin/sudo /sbin/shutdown -r now"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    print output

def playSound(snd_file):
    snd_file = AUDLIB + snd_file + '.mp3'
    snd = subprocess.Popen(['omxplayer', '-o', 'hdmi', snd_file])
    time.sleep(1)
    snd.communicate('q')

def getDelta(in_time, out_time):
    t1 = in_time.split(":")
    t2 = out_time.split(":")
    h1 = int(t1[0])
    h2 = int(t2[0])
    m1 = int(t1[1])
    m2 = int(t2[1])
    s1 = int(t1[2])
    s2 = int(t2[2])

    total = (3600*h2 + 60*m2 + s2) - (3600*h1 + 60*m1 + s1)
    h = int(math.floor(total/3600))
    total = total-(h*3600)
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
    if runCommand(t) == "None":
        try:
                
            Name = getName(t)
            Timecard = getTimecard(Name)
            now = getTime();

            printToLog(Name, now)

            if timecardFound(Name):                    
                with open(Timecard) as ts:
                    times = ts.read().splitlines()
            
                if times[len(times)-1].count(":") >= 4:
                    login(Name)
                else:
                    logout(Name)
            else:
                login(Name)
        except ValueError:
            print("Error unknown tag %s" % (t))
    

def printToScreen(text):
    printToFile(DISPLAY, text, True)

def actionOnTagLost(e):
    #TODO  performed once when tag is out of range
    time.sleep(1)

def calculateHours(time):
    t = time.split(":")
    h = float(t[0])
    m = float(t[1])
    s = float(t[2])
    
    hours = (h*3600 + m*60 + s) /3600
    str_h = str(hours)
    str_h = str_h[0:4]
    
    return(str_h)

    
def printToLog(Name, time):
    time_msg = Name + " , {};".format(time.strftime('%m/%d/%y %H:%M:%S'))
    printToFile('/home/pi/Desktop/Sign-In Script/log/log' + FILEFORMAT, time_msg, False)


def printToFile(fileName, text, overwrite):
    try:
        if overwrite:
            file = open(fileName, "w+")
            file.seek(0)
            file.truncate()
            file.write(text)
            file.close
        else:
            file = open(fileName, "a")
            file.write(text)
            file.close
    except ValueError:
        print("Error unknown tag %s" % (e.tag))

def runCommand(tag):
    command = "None"
    command = getCommand(tag)
    if command != "None":
        try:
            if os.path.isfile(command):
                subprocess.call(['lxterminal', '-e', 'sudo', command])
                playSound('hurry')
        except Exception as e:
            print(e)
    return command

#Event Handler Callback Functions
def RFIDAttached(e):
    attached = e.device
    actionOnAttach(e)
    print("RFID %i Attached!" % (attached.getSerialNum()))
         
def RFIDDetached(e):
    detached = e.device
    actionOnDetach(e)
    print("RFID %i Detached!" % (detached.getSerialNum()))
         
def RFIDError(e):
    try:
        source = e.device
        print("RFID %i: Phidget Error %i: %s" % (source.getSerialNum(), e.eCode, e.description))
    except PhidgetException as e:
        print("Phidget Exception %i: %s" % (e.code, e.details))
         
def RFIDTagGained(e):
    source = e.device
    RFID.setLEDOn(1)
    actionOnTagFound(e)
    
         
def RFIDTagLost(e):
    source = e.device
    RFID.setLEDOn(0)
    actionOnTagLost(e)

def init_anykey():
    global Old_settings
    Old_settings = termios.tcgetattr(sys.stdin)
    new_settings = termios.tcgetattr(sys.stdin)
    new_settings[3] = new_settings[3] & ~(termios.ECHO | termios.ICANON)
    new_settings[6][termios.VMIN] = 0
    new_settings[6][termios.VTIME] = 0
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, new_settings)


def term_anykey():
    global Old_settings
    if Old_settings:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, Old_settings)


def getKey():
    ch_set = []
    ch = os.read(sys.stdin.fileno(), 1)
    while ch != None and len(ch) > 0:
        ch_set.append( ord(ch[0]))
        ch = os.read(sys.stdin.fileno(), 1)
    return ch_set

#Main Program Code
try:
    RFID.setOnAttachHandler(RFIDAttached)
    RFID.setOnDetachHandler(RFIDDetached)
    RFID.setOnErrorhandler(RFIDError)
    RFID.setOnTagHandler(RFIDTagGained)
    RFID.setOnTagLostHandler(RFIDTagLost)

    print("Waiting for attach....")
    RFID.waitForAttach(10000)

    print("Turning on the RFID antenna....")
    RFID.setAntennaOn(True)
         
    print("Press Enter to quit....")

    #TODO constant run code here

    
    init_anykey()
    flag = True
    entry = ""
    while flag == True:
        time.sleep(.25)

        key = getKey()


# 55 56 57   
# 52 53 54
# 49 50 51 10
# 48


        if not key == None:
            key_str = str(key).replace("[", "")
            key_str = key_str.replace("]", "")
            key_str = key_str.replace(",", "")

            #entry = entry + str(count)            
            s = str(key_str[0:2])
            
            if s == "48": entry = entry + "0"
            if s == '49': entry = entry + "1"
            if s == '50': entry = entry + "2"
            if s == '51': entry = entry + "3"
            if s == '52': entry = entry + "4"
            if s == '53': entry = entry + "5"
            if s == '54': entry = entry + "6"
            if s == '55': entry = entry + "7"
            if s == '56': entry = entry + "8"
            if s == '57': entry = entry + "9"
            if s != "": printToFile(DISPLAY, entry, True)
        else:
            s = ''    

        if len(entry) >= 4:
            try:
                
                Name = getNameByPin(entry)
                if Name != "None":
                    Timecard = getTimecard(Name)
                    now = getTime();

                    printToLog(Name, now)

                    if timecardFound(Name):                    
                        with open(Timecard) as ts:
                            times = ts.read().splitlines()
                            
                        if times[len(times)-1].count(":") >= 4:
                            login(Name)
                        else:
                            logout(Name)
                    else:
                        login(Name)
                else:
                        playSound("error")
            except ValueError:
                print("Error with pin entry")
            entry = ""
            printToFile(DISPLAY, "", True)





        
        #if s == "10":
        #    flag = False

    print("Key pressed. Leaving")
    
    print("Closing...")
    try:
        RFID.closePhidget()
    except PhidgetException as e:
        print("Phidget Exception %i: %s" % (e.code, e.details))
        print("Error closing Phidget....")
        exit(1)

except PhidgetException as e:    
    print("Phidget Exception %i: %s" % (e.code, e.details))
         
print("Done.")
exit(0)
