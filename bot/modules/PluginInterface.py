import os, sys, traceback, inspect, imp, stat
import LogLib





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
  def __init__(self, plugin, listOfMissingPlugins):
    self.plugin = plugin
    self.listOfMissingPlugins = listOfMissingPlugins
  def __str__(self):
    return("Plugin %s cannot be loaded, because the following dependant plugins are missing: %s" % (self.plugin.pluginName, string.join(self.listOfMissingPlugins, ", ")))





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
      return self.procedure(self.plugin.object, *args)
    except Exception, exception:
      LogLib.log.addException("A plugin raised an exception!", exception)
      raise PluginExceptionError(self.plugin, exception)





#---------------------------------------------------------------------------------
#  PLUGIN
#    Represents a single plugin. These objects are parts of a list in Pluginfile.
#---------------------------------------------------------------------------------
class Plugin:
  """ Wraps a dynamically loaded plugin-class. """
  def __init__(self, object, pluginFile):
    self.pluginName = object.__class__.__name__
    self.handlers = []
    self.pluginFile = pluginFile
    self.object = object
    
  def registerEventHandlers(self, pluginInterface):
    pluginInterface.registerPlugin(self)
    for (name,funcobj) in self.object.__class__.__dict__.items():
      if(name[:2] == "on"):
        handler = EventHandler(self, funcobj, name)
        self.handlers.append(handler)
        pluginInterface.registerEventHandler(handler)
        LogLib.log.add(LogLib.LOGLVL_DEBUG, "INFO: added eventhandler " + name + " for " + self.pluginName)
        
  def dispose(self, pluginInterface):
    # unregister the plugin itself
    pluginInterface.unregisterPlugin(self)

    # unregister it's event handlers
    for handler in self.handlers:
      pluginInterface.unregisterEventHandler(handler)

    # if the plugin has a destructor, call it
    try:
        self.object.dispose()
    except:
        pass





#---------------------------------------------------------------------------------
#  PLUGIN FILE
#    Represents a file containing one or more plugins.
#---------------------------------------------------------------------------------
class PluginFile:
  def __init__(self, filepath, pluginInterface):
    self.filepath = filepath
    self.pluginInterface = pluginInterface
    self.module = None
    self.plugins = []
    self.lastModified = os.stat(filepath)[stat.ST_MTIME]
  
  def dispose(self):
    # remove module from sys.modules so that if/when the plugin is reloaded, 
    # it is not retrieved from the cache, but read from disk
    if self.module:
      del sys.modules[self.module.__name__]
    for plugin in self.plugins:
      plugin.dispose(self.pluginInterface)

  def removePlugin(self, plugin):
    plugin.dispose(self.pluginInterface)
    self.plugins.remove(plugin)

  def instantiatePlugins(self):
    # Load the module
    moduleName = os.path.splitext(os.path.split(self.filepath)[1])[0]
    try:
      self.module = imp.load_source(moduleName, self.filepath)
    except Exception, exception:
      LogLib.log.addException("Plugin raised exception during load:", exception)
      raise PluginLoadError()

    # check dependencies
    for (itemname, item) in self.module.__dict__.items():             # iterate over all classes
      if inspect.isclass(item) and itemname[-6:] == "Plugin":         # make sure it's even a plugin
        pluginClass = item                                            # use pluginClass identifier
        try:                                                          # try to ...
          dependencies = pluginClass.getDependencies()                # ... get the dependencies
        except AttributeError:                                        # if this fails ...
          break                                                       # then it's okay, it just means the plugin doesn't declare any dependencies
        except TypeError:                                             # if this fails ...
          break                                                       # then it's okay, it just means the plugin doesn't declare getDependencies() as a classmethod
        missingDependencies = []                                      # missingDependencies is used to store the dependencies that are missing
        for dep in dependencies:                                      # iterate over all dependencies
          if(not self.pluginInterface.getPluginByClassname(dep)):     # if that plugin is not loaded ...
            missingDependencies.append(dep)                           # ... then add it to the list
        if(len(missingDependencies) > 0):                             # if there are any missing ...
          raise MissingDependenciesError(itemname, missingDependencies)         # ... raise an exception

    # find all its plugin classes
    for (itemname, item) in self.module.__dict__.items():
      if inspect.isclass(item) and itemname[-6:] == "Plugin":      
        pluginClass = item

        try:
          # instantiate plugin class and wrap it in a Plugin-object
          #   if a constructor exists and it has two parameters (self, pluginInterface), call it with the pluginInterface as argument
          if (("__init__" in pluginClass.__dict__) and 
             ((len(inspect.getargspec(pluginClass.__dict__["__init__"])[0]) == 2))):
            plugin = Plugin(pluginClass(self.pluginInterface), self)
          #   otherwise, call the argument-less constructor
          else:
            plugin = Plugin(pluginClass(), self)
          plugin.registerEventHandlers(self.pluginInterface)
          self.plugins.append(plugin)
        except Exception, exception:
          LogLib.log.addException("Plugin raised exception during instantiation:", exception)
          raise PluginLoadError()

  def __nonzero__(self):
    return bool(self.module)

  def getPluginNames(self):
    """ Returns a list of the names of the plugins in this file """
    return [plugin.pluginName for plugin in self.plugins]





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
#
#---------------------------------------------------------------------------------
#      PluginInterface Public interface
#---------------------------------------------------------------------------------  
  def __init__(self, pluginsDirectory):
    if not os.path.exists(pluginsDirectory):
      raise Exception("The plugins directory: " + pluginsDirectory + " doesn't exist!")
    self.pluginsDirectory = pluginsDirectory
    self.pluginFileRepository = {} # dict of filepath  -> PluginFile
    self.eventHandlers = {}        # dict of eventName -> EventHandlerRepository
    self.plugins = {}              # dict of className -> Plugin
    self.botcore = None

  def dispose(self):
    for (filepath, pluginfile) in self.pluginFileRepository.items():
      pluginfile.dispose()

  def registerInformTarget(self, botcore):
    self.botcore = botcore

  def fireEvent(self, eventname, *args):
    if eventname in self.eventHandlers:
      try:
        self.eventHandlers[eventname].fireEvent(*args)
      except PluginExceptionError, exception:
        LogLib.log.add(LogLib.LOGLVL_DEBUG, "Removing erroneous plugin '" + exception.plugin.pluginName + "'")
        exception.plugin.pluginFile.removePlugin(exception.plugin)
        if(self.botcore):
          self.botcore.informErrorRemovedPlugin(exception.plugin.pluginName)
        else:
          raise Exception("ERROR: botcore isn't loaded, so I can't inform anyone of that failed plugin!")



  def updatePlugins(self, shallNotify=True):
    """ Searches for new, updated and removed plugins """
    loadedPluginsList = []
    reloadedPluginsList = []
    removedPluginsList = []

    # iterate over all currently loaded plugin files
    for (filepath, pluginfile) in self.pluginFileRepository.items():
      # If the plugin-file has been deleted
      if not os.path.exists(filepath):
        removedPluginsList.extend(pluginfile.getPluginNames())
        self.unloadPluginFile(filepath)

      # if the plugin-file has been modified
      elif pluginfile.lastModified != os.stat(filepath)[stat.ST_MTIME]:
        self.unloadPluginFile(filepath)
        pluginfile = self.loadPluginFile(filepath)
        if pluginfile: # if loaded successfully
          reloadedPluginsList.extend(pluginfile.getPluginNames())

    # collect a list of files I need to load
    pluginfilesToLoad = []
    filenames = [filename for filename in os.listdir(self.pluginsDirectory) if filename[-9:] == "Plugin.py"]
    for filepath in [os.path.join(self.pluginsDirectory, filename) for filename in filenames]:
      if not filepath in self.pluginFileRepository:
        pluginfilesToLoad.append(filepath)
    
    # load the files if their dependencies are loaded
    lastLength = len(pluginfilesToLoad)+1
    while((len(pluginfilesToLoad) > 0) and (lastLength > len(pluginfilesToLoad))):
        lastLength = len(pluginfilesToLoad)
        for filepath in pluginfilesToLoad:
            try:
                pluginfile = self.loadPluginFile(filepath)
                if pluginfile:   # if loaded successfully
                    loadedPluginsList.extend(pluginfile.getPluginNames())
                pluginfilesToLoad.remove(filepath)
            except MissingDependenciesError, exception:
                LogLib.log.add(LogLib.LOGLVL_DEBUG, "Loading of plugin file %s has been delayed because of missing dependencies." % (filepath))
    if(len(pluginfilesToLoad) > 0):
        notLoadedDueToMissingDependenciesPluginsList = pluginfilesToLoad
    else:
        notLoadedDueToMissingDependenciesPluginsList = []

    # notify the botcore if requested
    if(shallNotify):
        if(self.botcore):
            self.botcore.informPluginChanges(loadedPluginsList, reloadedPluginsList, removedPluginsList, notLoadedDueToMissingDependenciesPluginsList)
        else:
            raise Exception("ERROR: botcore isn't loaded yet, so I can't inform anyone of that failed plugin!")



  def getPluginByClassname(self, classname):
    if classname in self.plugins:
      return self.plugins[classname].object
    else:
      return None



  def getPluginNames(self):
    """ Returns a list of names of all loaded plugins """
    return [plugin.pluginName for plugin in self.plugins.values()]



  def getPlugins(self):
    """ Returns a list of instances of all loaded plugins """
    return [plugin.object for plugin in self.plugins.values()]
    
    
    
#---------------------------------------------------------------------------------
#      PluginInterface module-internal methods
#---------------------------------------------------------------------------------  
  def registerEventHandler(self, handler):
    if not handler.eventName in self.eventHandlers:
      self.eventHandlers[handler.eventName] = EventHandlerRepository()
    self.eventHandlers[handler.eventName].addHandler(handler)
  def unregisterEventHandler(self, handler):
    self.eventHandlers[handler.eventName].removeHandler(handler)
    
  def registerPlugin(self, plugin):
    self.plugins[plugin.pluginName] = plugin
  def unregisterPlugin(self, plugin):
    del self.plugins[plugin.pluginName]  
  
  def loadPluginFile(self, filepath):
    if not os.path.exists(filepath):
      raise Exception("PluginInterface was asked to load " + filepath  + ", but that file doesn't exist!")
    try:
      LogLib.log.add(LogLib.LOGLVL_DEBUG, "adding plugin file to repository: " + filepath)
      # load the file
      pluginFile = PluginFile(filepath, self)
      pluginFile.instantiatePlugins()
    except PluginLoadError:
      LogLib.log.add(LogLib.LOGLVL_DEBUG, "Removing erroneous plugin file '" + filepath + "'")
      if(self.botcore):
          self.botcore.informRemovedPluginDuringLoad(filepath)
      else:
          raise Exception("ERROR: botcore isn't loaded, so I can't inform anyone of that failed plugin!")
    self.pluginFileRepository[filepath] = pluginFile
    return pluginFile      

  def unloadPluginFile(self, filepath):
    if(filepath in self.pluginFileRepository):
      LogLib.log.add(LogLib.LOGLVL_DEBUG, "removing plugin file from repository: " + filepath)
      self.pluginFileRepository[filepath].dispose()
      del self.pluginFileRepository[filepath]
    else:
      LogLib.log.add(LogLib.LOGLVL_DEBUG, "this plugin file can't be removed because it isn't in the repository: " + filepath)
