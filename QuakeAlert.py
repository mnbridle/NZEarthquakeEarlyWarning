#!/usr/bin/python3

# Quake alert!
# Matthew Bridle, @midnightwarrior

# What it does:

# This software queries the GeoNet API very often, and if there's a severe
# quake detected, then it beeps. Kinda like a pre-emptive quake warning
# system.

# This version v16.11b15e
# Project started 15 November 2016

# Changelog:
# v16.11b15b - fixed some small bugs
# v16.11b15c - message format changes, it now tells you whether the message
#              is new or an update
# v16.11b15d - Performance improvements - sleep for a bit then check the 
#              locally stored quake list
# v16.11b15e - Sends push notifications

import json
import urllib.request
import pprint
import time
from datetime import datetime, timedelta
from threading import Timer
from time import sleep
import os

def main():

  rt = RepeatedTimer(15, getLatestQuakes) # it auto-starts, no need of rt.start()

  try:
    print("Quake Alert has started.")
    quakeData = {}

    while(1):
      sleep(0.1)
      # Keep checking returned objects
      if(rt.isUpdated()):
        #print("Updated!")
        newData = rt.getReturnedObject()

        for publicID in newData.keys():
          try:
            # Copy raw dict for compare
            quakeDataCmp = {}
            for key in quakeData[publicID].keys():
              if(key != "isUnread" and key != "displayed" and key != "status"):
                quakeDataCmp[key] = quakeData[publicID][key]

            if(quakeDataCmp != newData[publicID]):
              #print(quakeDataCmp)
              #print(newData[publicID])
              #print("Updated quake - ID: %s" % publicID)
              isDisplayed = quakeData[publicID]["displayed"]
              quakeData[publicID] = newData[publicID]
              quakeData[publicID]["displayed"] = isDisplayed
              quakeData[publicID]["isUnread"] = True
              quakeData[publicID]["status"] = "Updated"
              #print(quakeData[publicID])
            else:
              # Event is already in the dictionary
              #print("Event already occurred - ID: %s" % publicID)
              pass

          except:
            #print("New event - ID: %s" % publicID)
            quakeData[publicID] = newData[publicID]
            quakeData[publicID]["isUnread"] = True
            quakeData[publicID]["status"] = "New"
            quakeData[publicID]["displayed"] = False
            #print(quakeData[publicID])
        #print(quakeData)

        # Do alert if criteria are met
        for publicID in quakeData.keys():
          quake = quakeData[publicID]
          # Get unread quakeData
          if(quake["isUnread"] == True):
            quakeData[publicID]["isUnread"] = False
            magnitude = quake["properties"]["magnitude"]
            mmi = quake["properties"]["mmi"]

            # Break these out into functions and do proper desktop notifications
            #print(quake)

            if(magnitude >= 4 and magnitude < 6 and mmi >= 4 and mmi < 6 or quake["displayed"]==True):
              quakeData[publicID]["displayed"] = True
              notifyQuake(publicID, quake)

            if(magnitude >= 6 or mmi >= 6):
              quakeData[publicID]["displayed"] = True
              notifyQuakeSevere(publicID, quake)

  finally:
    rt.stop() # better in a try/finally block to make sure the program ends!

def notifyQuake(publicID, quake):
  # Calculate time since quake
  currentTime = int(time.time())
  rawQuakeTimeStr = quake["properties"]["time"]
  rawQuakeTime = "%s.%s000" % (rawQuakeTimeStr.split(".")[0], rawQuakeTimeStr.split(".")[1].split("Z")[0])
  quakeTimestamp = totimestamp(datetime.strptime(rawQuakeTime, "%Y-%m-%dT%H:%M:%S.%f"))
  timeSinceQuake = currentTime - quakeTimestamp
  print("**********      QUAKE!      **********")
  print("Status: %sID: %s" % ("{:<15}".format(quake["status"]), publicID))
  print("Magnitude: %.1f" % quake["properties"]["magnitude"])
  print("Depth: %.0f km" % quake["properties"]["depth"])
  print("mmi: %i" % quake["properties"]["mmi"])
  print("Location: %s" % quake["properties"]["locality"])
  print("Occured %.0f seconds ago\n\n" % timeSinceQuake)
  #quakeData[publicID]["displayed"] = True

  notification = "EQ %.0f seconds ago - mag%.1f, %.0fkm, %s, mmi%i" % (timeSinceQuake,
                                                                       quake["properties"]["magnitude"],
                                                                       quake["properties"]["depth"],
                                                                       quake["properties"]["locality"],
                                                                       quake["properties"]["mmi"])

  #sendMobileNotification(notification)



def notifyQuakeSevere(publicID, quake):
  currentTime = int(time.time())
  rawQuakeTimeStr = quake["properties"]["time"]
  rawQuakeTime = "%s.%s000" % (rawQuakeTimeStr.split(".")[0], rawQuakeTimeStr.split(".")[1].split("Z")[0])
  quakeTimestamp = totimestamp(datetime.strptime(rawQuakeTime, "%Y-%m-%dT%H:%M:%S.%f"))
  timeSinceQuake = currentTime - quakeTimestamp
  print("**********      MAJOR QUAKE!      **********")
  print("Status: %sID: %s" % ("{:<15}".format(quake["status"]), publicID))
  print("Magnitude: %.1f" % quake["properties"]["magnitude"])
  print("Depth: %.0f km" % quake["properties"]["depth"])
  print("mmi: %i" % quake["properties"]["mmi"])
  print("Location: %s" % quake["properties"]["locality"])
  print("Occured %.0f seconds ago\n\n" % timeSinceQuake)
  #quakeData[publicID]["displayed"] = True
  mmi = quake["properties"]["mmi"]
  os.system('play --no-show-progress --null --channels 1 synth %s sine %f' % ( 1+((mmi-6)*2), 500))

  # Send notification with information

  notification = "EQ %.0f seconds ago - mag%.1f, %.0fkm, %s, mmi%i" % (timeSinceQuake,
                                                                       quake["properties"]["magnitude"],
                                                                       quake["properties"]["depth"],
                                                                       quake["properties"]["locality"],
                                                                       quake["properties"]["mmi"])

  sendMobileNotification(notification)



def getLatestQuakes(minimumIntensity=0, checkingInterval=15):
  # Get current timestamp
  currentTime = int(time.time())
  #print("Checking for updates")

  with urllib.request.urlopen('https://api.geonet.org.nz/quake?MMI=%i' % minimumIntensity) as response:
    res = response.read()
  apiResponse = json.loads(res.decode("utf-8"))

  # Sort through this, convert the timestamps
  allQuakes = apiResponse["features"]
  recentQuakes = {}
  for quake in allQuakes:
    # Convert time
    rawQuakeTimeStr = quake["properties"]["time"]
    rawQuakeTime = "%s.%s000" % (rawQuakeTimeStr.split(".")[0], rawQuakeTimeStr.split(".")[1].split("Z")[0])
    quakeTimestamp = totimestamp(datetime.strptime(rawQuakeTime, "%Y-%m-%dT%H:%M:%S.%f"))
    publicID = quake["properties"]["publicID"]

    if(currentTime - quakeTimestamp <= 600):
      # Quake occurred very recently
      #recentQuakes[quakeTimestamp] = quake
      recentQuakes[publicID] = quake
      #print("Quake!")

  return(recentQuakes)




# This code from @MestreLion on StackOverflow - slightly modified to take return
# values

def totimestamp(dt, epoch=datetime(1970,1,1)):
    td = dt - epoch
    # return td.total_seconds()
    return (td.microseconds + (td.seconds + td.days * 86400) * 10**6) / 10**6 


class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer         = None
        self.interval       = interval
        self.function       = function
        self.args           = args
        self.kwargs         = kwargs
        self.is_running     = False
        self.returnedObject = None
        self.newUpdate      = False

        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.returnedObject = self.function(*self.args, **self.kwargs)
        self.newUpdate = True

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

    def isUpdated(self):
        return(self.newUpdate)

    def getReturnedObject(self):
        self.newUpdate = False
        return(self.returnedObject)

def sendMobileNotification(notstr):
  # APIKey for SimplePush goes here
  APIKey = ""
  request = "https://api.simplepush.io/send/%s/%s/event/eq" % (APIKey, notstr)
  try:
    with urllib.request.urlopen(request) as response:
      res = response.read()
  except:
    print("Request didn't work, URL: %s" % request)



main()
