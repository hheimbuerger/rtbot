import sys, inspect, imp, operator, util, logging, traceback
from lib.path import path

# Vocabulary
# classname - the name of the plugin class in the plugin file (eg. SeenPlugin is the
#             classname for the plugin defined in seenplugin.py
# enabled   - if a plugin is enabled, then it will process events if all its dependencies
#             are online. This property is persistent
# online    - a plugin is online if it's enabled and all its dependencies are online.
#             This means that it's processing events as expected

#---------------------------------------------------------------------------------
#  PLUGIN INTERFACE EXCEPTION CLASSES
#---------------------------------------------------------------------------------
class PluginExceptionError(Exception):
    """ Raised when a plugin raises an exception """
    def __init__(self, plugin, innerException):
        self.plugin = plugin
        self.innerException = innerException
    def __str__(self):
        return("Plugin " + self.plugin.pluginName + " caused the following exception:\n\n" + str(self.innerException))

class PluginLoadError(Exception):
    pass

class MissingDependenciesError(Exception):
    """ Raised when a plugin is missing one or more dependencies """
    pass

#---------------------------------------------------------------------------------
#  PRIORITIES
#    ...
#---------------------------------------------------------------------------------
class Priorities:
    # class variables
    PRIORITY_VERYLOW = 1
    PRIORITY_LOW = 2
    PRIORITY_NORMAL = 3
    PRIORITY_HIGH = 4
    PRIORITY_VERYHIGH = 5
    
    # Decorator for setting the priority of plugin eventhandlers
    @staticmethod
    def prioritized(priority):
      def decorator(func):
        func.priority = priority
        return func
      return decorator
    
    # reads the decorator (if existing) and returns the priority of the function (event-handler)
    # (or PRIORITY_NORMAL if no priority was specified with a decorator)
    @staticmethod
    def getPriority(function):
        return(getattr(function, "priority", Priorities.PRIORITY_NORMAL))


#---------------------------------------------------------------------------------
#  EVENT HANDLER
#    A callable class that wraps a plugin's event-procedures
#---------------------------------------------------------------------------------
class EventHandler:
    """ A callable class that wraps a plugin's event-procedures """
    def __init__(self, plugin, procedure, eventName):
        self.plugin = plugin
        self.procedure = procedure
        self.eventName = eventName
        self.priority = Priorities.getPriority(procedure) #getattr(procedure, "priority", 3)

    def __call__(self, *args):
        try:
            return self.procedure(self.plugin.pluginObject, *args)
        except Exception, exception:
            logging.exception("The plugin %s raised an exception in the eventhandler %s", self.plugin.pluginName, self.eventName)
            raise PluginExceptionError(self.plugin, exception)



#---------------------------------------------------------------------------------
#  PLUGIN
#---------------------------------------------------------------------------------
class Plugin:
    """ Wraps a dynamically loaded plugin-class. """

    ## CREATION AND DESTRUCTION
    ##############################
    
    def __init__(self, pluginInterface, pluginFile):
        
        self.pluginFile = pluginFile
        self.filepath = pluginFile.filepath
        self.pluginInterface = pluginInterface
        
        self.module = None       # holds the module loaded from this python file
        self.pluginObject = None # holds the instance of the plugin class in the file
        self.pluginClass = None
        self.pluginName = None
        self.handlers = []       # the event handlers that we register
        
        self.dependenciesAvailable = False
        
        self.dependencies = {}  # dict of classname -> plugin
        self.dependents = set()
        
        self.loadPluginObject()
        self.notifyDependencyChange()
        
    def addDependent(self, plugin):
        self.dependents.add(plugin)
    def removeDependent(self, plugin):
        self.dependents.remove(plugin)

    def hasDependency(self, name):
        return name in self.dependencies or reduce(operator.__or__, [dependency.hasDependency(name) for dependency in self.dependencies.values()], False)
       
    def dispose(self):
        self.putOffline()
        self.pluginInterface.unregisterPlugin(self)
        # remove module from sys.modules so that if/when the plugin is reloaded, 
        # it is not retrieved from the cache, but read from disk
        if self.module:
            del sys.modules[self.module.__name__]

    def notifyDependencyChange(self, changes = {}):
        "Called when our dependencies have changed"
        logging.debug("DependencyChange for %s: %s" % (self.pluginName, changes))
        if not changes:
            changes = dict(zip( self.dependencyClassNames, [self.pluginInterface.handleDependency(dep) for dep in self.dependencyClassNames]))
        self.dependencies.update(changes)
        for plugin in changes.values():
            plugin.addDependent(self)
            
        self.notifyDependencyAvailabilityChange()
            
    def notifyDependencyAvailabilityChange(self):
        "Called when our dependencies have changed their availability"
        logging.debug("Dependencies changed for plugin %s" % self.pluginName)
        newAvailability = reduce(operator.__and__, [plugin.online() for plugin in self.dependencies.values()], True)
        logging.debug("dependencies were: %s. Now they are %s" % (self.dependenciesAvailable, newAvailability))
        if newAvailability != self.dependenciesAvailable:
            self.dependenciesAvailable = newAvailability
            if self.dependenciesAvailable:          
                self.putOnline()
            else:
                self.putOffline()

    ## ACTIVATION AND AVAILABILITY
    ################################
        
    def putOnline(self):
        "Brings the plugin online again"
        logging.info("Bringing plugin %s online" % self.pluginName)
        self.instantiateObject()
        self.registerEventHandlers()        # register our handlers again
        for plugin in self.dependents:
            plugin.notifyDependencyAvailabilityChange()                            
            
    def putOffline(self):
        "Deactivates the plugin"
        logging.info("Bringing plugin %s offline" % self.pluginName)
        self.disposePluginObject()
        self.unregisterEventHandlers()
        for plugin in self.dependents:
            plugin.notifyDependencyAvailabilityChange()
            
    def online(self):
        return self.dependenciesAvailable

    # INTERNAL METHODS
    
    def registerEventHandlers(self):
        for handler in self.handlers:
            self.pluginInterface.registerEventHandler(handler)  
            logging.debug("Added handler for event %s belonging to the plugin %s", handler.eventName, self.pluginName)
    
    def unregisterEventHandlers(self):
        for handler in self.handlers:
            self.pluginInterface.unregisterEventHandler(handler)   

    ## PARSING OF PY-FILE
    
    def loadPluginObject(self):
        """dynamically loads the plugin py-file, instantiates the plugin and registers
        the event handlers. Raises a PluginLoadException if the load wasn't successful"""
        try:
            self.loadModule()
            self.findClass()
        except:
            logging.debug("Error during plugin load in the file %s", self.filepath)
            raise
        self.pluginInterface.registerPlugin(self.pluginName, self)

    def disposePluginObject(self):
        logging.debug("disposing %s" % self.pluginName)
                # if the plugin has a destructor, call it
        if self.pluginObject:
            try:
                self.pluginObject.dispose()
            except:
                pass
        self.pluginObject = None
        
    def loadModule(self):
        try:
            self.module = imp.load_source(self.filepath.namebase, self.filepath)
        except Exception, e:
            logging.exception("Plugin raised exception during load")
            raise PluginLoadError(e)

    def findClass(self):
        for (itemname, item) in self.module.__dict__.items():             # iterate over all classes
            if inspect.isclass(item) and itemname[-6:] == "Plugin":         # make sure it's even a plugin
                self.pluginClass = item                                            # use pluginClass identifier
                break                                                 # There is only one plugin class per file
        else:
            raise PluginLoadError("Can't find plugin class")

        try:                                                          # try to ...
            self.dependencyClassNames = set(self.pluginClass.getDependencies()) # ... get the dependencies
        except AttributeError:                                        # if this fails ...
            self.dependencyClassNames = set()                                  # then it's okay, it just means the plugin doesn't declare any dependencies
        except TypeError:                                            # if this fails ...
            self.dependencyClassNames = set()                                  # then it's okay, it just means the plugin doesn't declare getDependencies() as a classmethod        
        except Exception, e:                                         # Handler for other exceptions raised by plugin
            raise PluginLoadError("Plugin raised exception when trying to determine dependencies")
        
        self.pluginName = self.pluginClass.__name__
        self.dependencies = dict(zip( self.dependencyClassNames, [self.pluginInterface.handleDependency(dep) for dep in self.dependencyClassNames]))
        
        logging.debug("Dependencies: %s" % str(self.dependencies))
        if self.hasDependency(self.pluginName):
            raise PluginLoadError("Circular dependency error in %s" % (self.pluginName,))
        
        # Find all the event handlers
        for (name,funcobj) in self.pluginClass.__dict__.items():
            if name[:2] == "on" and callable(funcobj) :
                handler = EventHandler(self, funcobj, name)
                self.handlers.append(handler)
        logging.debug("Found %i event handlers for plugin %s" % (len(self.handlers), self.pluginName))
    
    def instantiateObject(self):
        try:
            #   if a constructor exists and it has two parameters (self, pluginInterface), call it with the pluginInterface as argument
            if  hasattr(self.pluginClass,"__init__") and len(inspect.getargspec(self.pluginClass.__init__)[0]) == 2:
                self.pluginObject = self.pluginClass(self.pluginInterface)
                
            else:  #   otherwise, call the argument-less constructor
                self.pluginObject = self.pluginClass()
        except Exception, e:
            logging.exception("Plugin raised exception during instantiation")
            raise PluginLoadError(e)

class MissingDependency:
    def __init__(self, name):
        self.pluginName = name
    def online(self):
        return False
    def hasDependency(self, name):
        return False
    def addDependent(self, plugin):
        pass
    def removeDependent(self, plugin):
        pass

class PluginFile:
    """Represents a *plugin.py file. The main point of this class is to manage the persistent
    flag that determines if the plugin is enabled or not."""
    
    ## PUBLIC INTERFACE
    def __init__(self, filepath, pluginInterface):
        self.filepath = filepath
        self.pluginInterface = pluginInterface
        self.lastModified = filepath.mtime
        self.enabled = False
        self.plugin = None
        self.setEnable(True)
        
    def dispose(self):
        if self.plugin:
            self.plugin.dispose()
        
    def setEnable(self, arg):
        """ Sets whether the plugin is enabled or not. enabled plugins
        process events. Deactivated plugins do not. This is a persistent 
        property (ie. it's pickled by the pluginInterface)"""
        if not arg == self.enabled:
            self.enabled = arg
            if arg:
                assert not self.plugin
                try:
                    self.loadPlugin()
                except PluginLoadError:
                    self.enabled = False
                    self.plugin = None
                except Exception:
                    logging.exception("Unexpected error during plugin load")
            else:
                assert self.plugin
                self.plugin.dispose()
                self.plugin = None
    
    def checkForUpdate(self):
        """Checks if there are any updates available for this plugin. Returns True if there were.
        Raises an exception if the file no longer exists"""
        if self.filepath.mtime != self.lastModified: # This line raises the exception
            self.setEnable(False)
            self.setEnable(True)
            return True
        
    def loadPlugin(self):
        self.plugin = Plugin(self.pluginInterface, self)
        self.lastModified = self.filepath.mtime        
        
    ## PICKLING METHODS
    def __getstate__(self):
        """Called by the pickle module for serialization"""
        state = self.__dict__.copy()
        state["plugin"] = None  # pick the fields that are suitable for serialization
        return state
    
    def __setstate__(self, dict):
        """Called by the pickle module for deserialization"""
        self.__dict__.update(dict)
        logging.debug("Deserializing plugin %s. Enabled: %s" % (self.filepath.namebase, self.enabled))
        if not self.filepath.exists():
            self.enabled = False
        if self.enabled:
            self.enabled = False
            self.plugin = None
            self.setEnable(True)

#---------------------------------------------------------------------------------
#  EVENT HANDLER REPOSITORY
#    The repository of plugin files that is used in one instance by the
#    plugin interface.
#---------------------------------------------------------------------------------
class EventHandlerRepository:
  """ Keeps track of all the procedures that handle a specific event """
  def __init__(self):
    self.handlers = []
  def addHandler(self, handler):
    self.handlers.append(handler)
    self.sortHandlers()
  def removeHandler(self, handler):
    try: self.handlers.remove(handler)
    except: pass

  # Static function for comparing priorities. This assumes that the handlers
  # have a priority attribute
  @staticmethod
  def compareHandlers(left, right):
    if   left.priority <  right.priority: return 1
    elif left.priority == right.priority: return 0
    else: return -1

  def sortHandlers(self):
    self.handlers.sort(self.compareHandlers)
  def fireEvent(self, *args):
    for procedure in self.handlers:
      # event handler procedures return true to abort processing
      if procedure(*args):
        break

#---------------------------------------------------------------------------------
#  PLUGIN INTERFACE
#    The main class of the plugin interface.
#---------------------------------------------------------------------------------
class PluginInterface:
#---------------------------------------------------------------------------------
#      PluginInterface Public interface
#---------------------------------------------------------------------------------
    pluginMetaData = path("resources/PluginMetaData.pickle")
    def __init__(self, pluginsDirectory):
        
        # Helper methods for pickling
        def persistent_id(obj):
            if isinstance(obj, PluginInterface):
                return "MyPersistentID"
        def persistent_load(persid):
            if persid == "MyPersistentID":
                return self
            
        self.pluginsDirectory = path(pluginsDirectory)
        if not self.pluginsDirectory.exists():
            raise Exception("The plugins directory: " + pluginsDirectory + " doesn't exist!")        
        
        self.botcore = None                            
        self.eventHandlers = {}     # dict of eventName -> EventHandlerRepository
        self.plugins = {}           # dict of pluginName -> Plugin
        # persistent dict of filename -> PluginFile
        self.pluginFiles = util.Archive(self.pluginMetaData, persistent_id, persistent_load)
        
    def dispose(self):
        self.pluginFiles.sync()

    def registerInformTarget(self, botcore):
        self.botcore = botcore

    def fireEvent(self, eventname, *args):
        if eventname in self.eventHandlers:
            try:
                self.eventHandlers[eventname].fireEvent(*args)
            except PluginExceptionError, exception:
                pluginName = exception.plugin.pluginName
                logging.info("Disabling erraneous plugin: %s", pluginName)
                if self.botcore:
                    self.botcore.informErrorRemovedPlugin("The plugin %s raised errors and is now disabled" % (pluginName))
                self.setPluginStateByClassname(pluginName, False)

    def updatePlugins(self, shallNotify=True):
        """ Searches for new, updated and removed plugins 
        shallNotify - true if the informTarget / botcore should be notified about
                      the changes"""
        logging.debug("Starting to update plugins")
        pluginsBefore = set(self.plugins.keys())  # for aggregating statistics. Keeps track of what plugins were before we make changes
        reloadedPlugins = set()
        # iterate over all our plugins and see if there are any changes
        for filename, pluginfile in self.pluginFiles.items():
            try:
                if pluginfile.checkForUpdate() : # if there was an update...
                    logging.info("reloaded the plugin file %s", filename)
                    reloadedPlugins.add(filename)
            except OSError, e:
                # file was not found
                self.pluginFiles[filename].dispose()
                del self.pluginFiles[filename]
                logging.info("The plugin file %s was deleted", filename)
        # Check if there are any new files
        for file in self.pluginsDirectory.files("*Plugin.py"):
            if not file.name in self.pluginFiles.keys():
                logging.info("New plugin file found: %s", file.name)
                self.pluginFiles[file.name] = PluginFile(file, self)
                if not self.pluginFiles[file.name].enabled:
                    self.botcore.informRemovedPluginDuringLoad("The plugin %s raised errors during load time and is now disabled" % (file.name))

        pluginsAfter = set(self.plugins.keys())
        loadedPlugins = pluginsAfter.difference(pluginsBefore)
        removedPlugins = pluginsBefore.difference(pluginsAfter)
        # notify the botcore if requested
        if(shallNotify):
            if(self.botcore):
                self.botcore.informPluginChanges(loadedPlugins, reloadedPlugins, removedPlugins, [])
            else:
                raise Exception("ERROR: botcore isn't loaded yet, so I can't inform anyone of that failed plugin!")

    def setPluginStateByFilename(self, pluginFilename, state):
        """Changes the state of a plugin that is specified by its file name. If state
        is true, then the plugin will be enabled and process events (if all its dependencies
        are available)"""
        if state:
            logging.debug("Activating pluginfile %s", pluginFilename)
        else:
            logging.debug("Deactivating pluginfile %s", pluginFilename)
        self.pluginFiles[pluginFilename].setEnable(state)

    def setPluginStateByClassname(self, pluginName, state):
        """Changes the state of a plugin that is specified by its class name. If state
        is true, then the plugin will be enabled and process events (if all its dependencies
        are available)"""
        if state:
            logging.debug("Activating plugin %s", pluginName)
        else:
            logging.debug("Deactivating plugin %s", pluginName)        
        self.plugins[pluginName].pluginFile.setEnable(state)

    def getPluginByClassname(self, classname):
        if classname in self.plugins and self.plugins[classname].online():
            return self.plugins[classname].pluginObject
        else:
            # Originally intended to raise exception here, since plugins shouldn't
            # ever get execution time when dependencies are down. But versionplugin
            # foiled that idea.
            #raise MissingDependenciesError("Some plugin has an undeclared dependency to '%s', which is currently unavailable" % (classname,))
            return None

    def handleDependency(self, pluginName):
        return self.plugins.get(pluginName, MissingDependency(pluginName))

    def getPluginNames(self):
        """ Returns a list of names of all loaded plugins """
        return self.plugins.keys()

    def getPlugins(self):
        """ Returns a list of instances of all loaded plugins """
        return [plugin.pluginObject for plugin in self.plugins.values()]
    
#---------------------------------------------------------------------------------
#      PluginInterface module-internal methods
#---------------------------------------------------------------------------------  
    def registerEventHandler(self, handler):
        logging.info("Registering event %s for plugin %s" % (handler.eventName, handler.plugin.pluginName))
        if not handler.eventName in self.eventHandlers:
            self.eventHandlers[handler.eventName] = EventHandlerRepository()
        self.eventHandlers[handler.eventName].addHandler(handler)
    def unregisterEventHandler(self, handler):
        self.eventHandlers[handler.eventName].removeHandler(handler)
        
    def registerPlugin(self, pluginName, plugin):
        logging.info("Registering the plugin %s" % pluginName)
        if pluginName in self.plugins:
            raise PluginLoadError("Plugin Name collision. Both the files %s and %s have plugins names %s", 
                                    plugin.filepath, self.plugins[pluginName].filepath, pluginName)
        self.plugins[pluginName] = plugin
        changes = {pluginName : plugin}
        for plugin in self.plugins.values():
            if plugin.hasDependency(pluginName):
                plugin.notifyDependencyChange(changes)

    def unregisterPlugin(self, plugin):
        logging.debug("Unregistering the plugin %s" % plugin.pluginName)
        del self.plugins[plugin.pluginName]
        changes = dict( [(plugin.pluginName, MissingDependency(plugin.pluginName))] )
        for p in self.plugins.values():        # Technically, the Plugin could do this by itself,
            if p.hasDependency(plugin.pluginName):    # but this way seems more symmetrical
                p.notifyDependencyChange(changes)