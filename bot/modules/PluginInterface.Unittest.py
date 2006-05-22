# Note: Should be run from the project root - modules\..
import unittest, os, time, logging
import Log
import coverage, colorize

from path import path

class FakeBot:
    def informPluginChanges(self, loadedPluginsList, reloadedPluginsList, removedPluginsList, unused):
        logging.critical("InformPluginChanges called. parameters: %s" % (str(locals()),))
        self.informPluginChangesCalled = True
    def informErrorRemovedPlugin(self, plugin):
        logging.critical("informErrorRemovedPlugin called. parameter: %s" % (plugin,))
        self.informErrorRemovedPluginCalled = True
    def informRemovedPluginDuringLoad(self, pluginfile):
        logging.critical("informRemovedPluginDuringLoad called. parameter: %s" % (pluginfile,))
        self.informRemovedPluginDuringLoadCalled = True

TestPluginDirectory = path("modules")
TestFiles = {}
TestFiles["TestPlugin.py"] = """
import random, logging
from modules import PluginInterface

class TestPlugin:
    def __init__(self, pluginInterface):
        logging.debug("PLUGIN: constructor called")

    @PluginInterface.Priorities.prioritized( PluginInterface.Priorities.PRIORITY_VERYHIGH )
    def onEvent(self, param1, param2):
        logging.debug("PLUGIN: event fired (" + str(param1) + "|" + str(param2) + ")")
        logging.debug("PLUGIN: random number: " + str(random.random()))

    def onFaultyEvent(self):
        print 1/0

    def getFourtyTwo(self):
        return 42"""

TestFiles["BarPlugin.py"] = """
class BarPlugin:
    def onEvent(self,param1, param2):
        raise Exception("Something bad happened")"""

TestFiles["FaultyPlugin.py"] = """This is not Python"""

TestFiles["DependencyPlugin.py"] = """
class DependencyPlugin:
    @staticmethod
    def getDependencies():
        return ["BarPlugin"]        
    def onEvent(self,a,b):
        return True # consume event
"""

TestFiles["CircularPlugin.py"] = """
from modules import PluginInterface
class BarPlugin:
    @staticmethod
    def getDependencies():
        return ["DependencyPlugin"]        
"""
        
def CreateTestFile(filename):
    logging.critical("writing test file: %s" % (filename,))
    stream = (TestPluginDirectory/filename).open("w")
    stream.write(TestFiles[filename])
def RemoveTestFile(filename):
    if (TestPluginDirectory/filename).exists():
        (TestPluginDirectory/filename).remove()
def RemoveTestFiles():
    for filename in TestFiles.keys():
        RemoveTestFile(filename)

class PluginInterfaceTestCase(unittest.TestCase):
    def testInitialState(self):
        print
        logging.info("********************************************")
        logging.info("********** TESTING INITIAL STATE ***********")
        logging.info("********************************************")
        
        if PluginInterface.pluginMetaData.exists():
            PluginInterface.pluginMetaData.remove()
        pi = PluginInterface("modules")
        self.assert_(len(pi.pluginFiles) == 0)
        self.assert_(pi.getPlugins() == [])

    def testErraneousPluginDir(self):
        self.assertRaises(Exception, lambda : PluginInterface("Nonexistant"))

    def testLoadTestClass(self):
        "Tries to load the test plugin"
        print
        logging.info( "********************************************")
        logging.info( "********** Testing the test plugin *********")
        logging.info( "********************************************")
        
        if PluginInterface.pluginMetaData.exists():
            PluginInterface.pluginMetaData.remove()        
        pi = PluginInterface("modules")
        fakebot = FakeBot()
        pi.registerInformTarget(fakebot)
        CreateTestFile("TestPlugin.py")
        try:  # wrap in try block to ensure file deletion
            pi.updatePlugins()
            self.assert_(fakebot.informPluginChangesCalled)
            self.assert_(pi.getPluginNames() == ["TestPlugin"])
            plugin = pi.getPluginByClassname("TestPlugin")
            self.assert_(plugin)
            self.assert_(plugin.getFourtyTwo() == 42)
            
            pi.fireEvent("onFaultyEvent")
            self.assert_(fakebot.informErrorRemovedPluginCalled)
        finally:
            RemoveTestFiles()

    def testFaultyPlugin(self):
        "Tries to load a plugin with syntax errors. Then replaces this with a correct one"
        print
        logging.info( "********************************************")
        logging.info( "********** testFaultyPlugin        *********")
        logging.info( "********************************************")  
        if PluginInterface.pluginMetaData.exists():
            PluginInterface.pluginMetaData.remove()      
        pi = PluginInterface("modules")
        fakebot = FakeBot()
        pi.registerInformTarget(fakebot)

        try:   # wrap in try block to ensure file deletion
            CreateTestFile("FaultyPlugin.py")
            pi.updatePlugins()
            self.assert_(fakebot.informRemovedPluginDuringLoadCalled, "Errors not detected when reading erroneous plugin")
            self.assert_(fakebot.informPluginChangesCalled)
            self.assert_(pi.getPluginNames() == [])
            self.assert_(len(pi.pluginFiles) == 1)
            
            time.sleep(2)
            RemoveTestFiles()
            CreateTestFile("BarPlugin.py")
            path("modules/BarPlugin.py").rename(path("modules/FaultyPlugin.py"))
            
            pi.updatePlugins()
            self.assert_(fakebot.informPluginChangesCalled, "informPluginChangesCalled not called after plugin change")
            self.assert_(len(pi.getPlugins()) == 1, "Not all plugins were registered after plugin change")
            self.assert_(pi.fireEvent("onEvent",3,4) == None, "Error when firing event")
        finally:
            RemoveTestFiles()
      
    def testPluginRemoval(self):
        "Checks if the plugin interface detects a removed plugin"
        print
        logging.info( "********************************************")
        logging.info( "********** testPluginRemoval        ********")
        logging.info( "********************************************")  
        if PluginInterface.pluginMetaData.exists():
            PluginInterface.pluginMetaData.remove()    
        pi = PluginInterface("modules")
        fakebot = FakeBot()
        pi.registerInformTarget(fakebot)
        
        try:
            CreateTestFile("BarPlugin.py")
            pi.updatePlugins()
            self.assert_(len(pi.getPlugins()) == 1)
            
            RemoveTestFiles()
            pi.updatePlugins()
            self.assert_(len(pi.getPlugins()) == 0, "Did not detect a removed file")
            self.assert_(fakebot.informPluginChangesCalled, "informPluginChangesCalled not called after plugin change")
        finally:
            RemoveTestFiles()
    
    def testPluginDependencies(self):
        logging.info( "********************************************")
        logging.info( "********** testPluginDependencies   ********")
        logging.info( "********************************************") 
        if PluginInterface.pluginMetaData.exists():
            PluginInterface.pluginMetaData.remove()
        pi = PluginInterface("modules")
        fakebot = FakeBot()
        pi.registerInformTarget(fakebot)
        
        try:
            CreateTestFile("DependencyPlugin.py")
            CreateTestFile("BarPlugin.py")
            pi.updatePlugins()
            self.assert_(len(pi.getPlugins()) == 2)
            self.assert_(pi.getPluginByClassname("BarPlugin"))
            self.assert_(pi.getPluginByClassname("DependencyPlugin"))
        finally:
            RemoveTestFiles()

    def testCyclicDependencies(self):
        logging.info( "********************************************")
        logging.info( "********** testCyclicDependencies   ********")
        logging.info( "********************************************") 
        if PluginInterface.pluginMetaData.exists():
            PluginInterface.pluginMetaData.remove()        
        pi = PluginInterface("modules")
        fakebot = FakeBot()
        pi.registerInformTarget(fakebot)
        try:
            CreateTestFile("DependencyPlugin.py")
            CreateTestFile("CircularPlugin.py")
            pi.updatePlugins()
            self.assertRaises(MissingDependenciesError, lambda: pi.getPluginByClassname("FooPlugin"))
            self.assertRaises(MissingDependenciesError, lambda: pi.getPluginByClassname("BarPlugin"))
        finally:
            RemoveTestFiles()
    def testEnabling(self):
        logging.info( "********************************************")
        logging.info( "********** testEnabling             ********")
        logging.info( "********************************************") 
        if PluginInterface.pluginMetaData.exists():
            PluginInterface.pluginMetaData.remove()        
        pi = PluginInterface("modules")
        fakebot = FakeBot()
        pi.registerInformTarget(fakebot)
        try:
            CreateTestFile("BarPlugin.py")
            CreateTestFile("DependencyPlugin.py")
            pi.updatePlugins()
            self.assert_(len(pi.getPlugins()) == 2)
            pi.setPluginStateByFilename("BarPlugin.py", False)
            self.assert_(len(pi.getPluginNames()) == 1)
            self.assertRaises(MissingDependenciesError, lambda: pi.getPluginByClassname("DependencyPlugin"))
            
            pi.setPluginStateByFilename("BarPlugin.py", True)
            self.assert_(len(pi.getPluginNames()) == 2)
            pi.getPluginByClassname("DependencyPlugin")
            pi.getPluginByClassname("BarPlugin")
        finally:
            RemoveTestFiles()
    def testPersistency(self):
        logging.info( "********************************************")
        logging.info( "********** testPersistency             ********")
        logging.info( "********************************************") 
        if PluginInterface.pluginMetaData.exists():
            PluginInterface.pluginMetaData.remove()        
        pi = PluginInterface("modules")
        fakebot = FakeBot()
        pi.registerInformTarget(fakebot)
        try:
            CreateTestFile("BarPlugin.py")
            pi.updatePlugins()
            self.assert_(len(pi.getPlugins()) == 1)
            pi.setPluginStateByFilename("BarPlugin.py", False)
            self.assert_(len(pi.getPluginNames()) == 0)
            self.assertRaises(MissingDependenciesError, lambda: pi.getPluginByClassname("BarPlugin"))
            
            pi.dispose()
            pi = PluginInterface("modules")
            fakebot = FakeBot()
            pi.registerInformTarget(fakebot)
            
            self.assert_(len(pi.pluginFiles) == 1)
            self.assert_(len(pi.getPluginNames()) == 0)
            self.assertRaises(MissingDependenciesError, lambda: pi.getPluginByClassname("BarPlugin"))
        finally:
            RemoveTestFiles()
def suite():
  return  unittest.TestSuite((unittest.makeSuite(PluginInterfaceTestCase)))

#if __name__ == '__main__':
coverage.erase()
coverage.start()
import PluginInterface
from PluginInterface import *
unittest.TextTestRunner(verbosity=2).run(suite())
coverage.stop()

# coverage analysis
f, s, m, mf = coverage.analysis("modules/plugininterface.py")
# output it in ./<module filename>.html
fo = file(os.path.basename(f)+'.html', 'wb')
# colorization
colorize.colorize_file(f, outstream=fo, not_covered=mf)
fo.close()
# print report on stdout
coverage.report("modules/plugininterface.py")
# erase coverage data
coverage.erase()