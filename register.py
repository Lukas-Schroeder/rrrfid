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
from random import randint


HOMEPATH = '/home/pi/Desktop/Sign-In Script/'
AUDLIB = HOMEPATH + 'aud/'
LOGPATH = HOMEPATH + 'log/'

HIDDENPATH = '/var/www/'
DISPLAY = HIDDENPATH + 'message.txt'
TAGS = HIDDENPATH + 'tag.txt'
COMMANDS = HIDDENPATH + 'commands.txt'
FILEFORMAT = '.odf'


TagsList=list()
with  open(TAGS) as f:
    TagsList = f.read().splitlines()

if len(TagsList) > 0:
    PinsList=list(range(0, len(TagsList)))
    for idx in range(0, len(TagsList)):
        assignment = TagsList[idx].split('=')
        if len(assignment)>2: PinsList[idx] = assignment[2]        
else:
    PinsList=list()

CommandsList=list()
with open(COMMANDS) as f:
    CommandsList = f.read().splitlines()


def generatePin():
    same = 1
    while same > 0:
        same = 0
        Pin = ""
        for bit in range(0,4):
            Pin = Pin + str(randint(0,9))
        for idx in range(0, len(TagsList)):
            if Pin == PinsList[idx]:
                same = same + 1
    return Pin

def getName(tag):
    Name = "None"
    for idx in range(0,len(TagsList)):
        assignee=TagsList[idx].split('=')
        if assignee[0]==tag:
            Name=assignee[1]
            break
    return Name

def printToFile(fileName, text, overwrite):
    isfile = os.path.isfile(fileName)
    overwrite = not (overwrite ^ isfile) or (overwrite & (not isfile))
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

name = ""
pin = generatePin()

while name=="":
    name = raw_input("Enter a name ")
    msg = name + "=" + pin
    
printToFile(HIDDENPATH+"tag.txt", msg, False)

exit(0)
