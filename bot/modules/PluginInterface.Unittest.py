# Note: Should be run from the project root - modules\..
# (LogLib needs to find its files...)
import unittest, os, time
from PluginInterface import *

class FakeBot:
    def informPluginChanges(self, loadedPluginsList, reloadedPluginsList, removedPluginsList):
      self.informPluginChangesCalled = True
    def informErrorRemovedPlugin(self, plugin):
      self.informErrorRemovedPluginCalled = True
    def informRemovedPluginDuringLoad(self, pluginfile):
      self.informRemovedPluginDuringLoadCalled = True

class PluginInterfaceTestCase(unittest.TestCase):
  def testInitialState(self):
    pi = PluginInterface("modules")
    self.assert_(pi.getPluginNames() == [])
    self.assert_(pi.getPlugins() == [])
  def testErraneousPluginDir(self):
    self.assertRaises(Exception, lambda : PluginInterface("Nonexistant"))
  def testLoadTestClass(self):
    "Tries to load the test plugin"
    pi = PluginInterface("modules")
    fakebot = FakeBot()
    pi.registerInformTarget(fakebot)
    pi.updatePlugins()
    self.assert_(fakebot.informPluginChangesCalled)
    self.assert_(pi.getPluginNames() == ["TestPlugin"])
    plugin = pi.getPluginByClassname("TestPlugin")
    self.assert_(plugin)
    self.assert_(plugin.getFourtyTwo() == 42)
    
    pi.fireEvent("onFaultyEvent")
    self.assert_(fakebot.informErrorRemovedPluginCalled)
    
    self.assert_(pi.getPluginNames() == [])
    self.assert_(pi.getPlugins() == [])
  def testFaultyPlugin(self):
    "Tries to load a plugin with syntax errors. Then replaces this with a correct one\n"
    try:
      filepath = os.path.join("modules", "FaultyPlugin.py")
      fp = file(filepath, "w")
      fp.write("This is not Python!")
      fp.close()
      
      pi = PluginInterface("modules")
      fakebot = FakeBot()
      pi.registerInformTarget(fakebot)
      
      pi.updatePlugins()
      self.assert_(fakebot.informRemovedPluginDuringLoadCalled, "Errors not detected when reading erroneous plugin")
      self.assert_(fakebot.informPluginChangesCalled)
      self.assert_(pi.getPluginNames() == ["TestPlugin"])
      
      time.sleep(2)
      fp = file(filepath, "w")
      fp.write("""
import modules.util
class FooPlugin:
  def onEvent(self,a,b):
    raise Exception("This shouldn't happen")
class BarPlugin:
  @modules.util.prioritized(5)
  def onEvent(self,a,b):
    return True # consume event
        """)
      fp.close()
      pi.updatePlugins()
      self.assert_(fakebot.informPluginChangesCalled, "informPluginChangesCalled not called after plugin change")
      self.assert_(len(pi.getPlugins()) == 3, "Not all plugins were registered after plugin change")
      self.assert_(pi.fireEvent("onEvent",3,4) == None, "Error when firing event")
    finally:
      os.remove(filepath)
      
  def testPluginRemoval(self):
    "Checks if the plugin interface detects a removed plugin"
    filepath = os.path.join("modules", "TempPlugin.py")
    fp = file(filepath, "w")
    fp.write("""print "Evaluating plugin code..." """)
    fp.close()
    try:
      pi = PluginInterface("modules")
      fakebot = FakeBot()
      
      pi.updatePlugins()
      pluginsBefore = len(pi.pluginFileRepository.keys())
      os.remove(filepath)
      pi.registerInformTarget(fakebot)
      pi.updatePlugins()
      self.assert_(pluginsBefore - len(pi.pluginFileRepository.keys()) == 1, "Did not detect a removed file")
      
      self.assert_(fakebot.informPluginChangesCalled, "informPluginChangesCalled not called after plugin change")
    finally:
      if os.path.exists(filepath):
        os.remove(filepath)
    
    
def suite():
  return  unittest.TestSuite((unittest.makeSuite(PluginInterfaceTestCase)))

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())