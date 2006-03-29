import random
import LogLib

class TestPlugin:
  def __init__(self, pluginInterface):
    print "PLUGIN: constructor called"

  def onEvent(self, param1, param2):
    print "PLUGIN: event fired (" + str(param1) + "|" + str(param2) + ")"
    print "PLUGIN: random number: " + str(random.random())

  def onFaultyEvent(self):
    print 1/0

  def getFourtyTwo(self):
    return(42)