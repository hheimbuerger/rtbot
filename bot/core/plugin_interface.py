import functools
import importlib
import inspect
import logging
import operator
import pickle
import sys
from pathlib import Path


def decorator(decorfunc):
   def wrapper(func):
      return lambda *args, **kwargs: decorfunc(func, *args, **kwargs)
   return wrapper

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
    def __init__(self, pluginWrapper, innerException):
        self.pluginWrapper = pluginWrapper
        self.innerException = innerException
    def __str__(self):
        return("Plugin " + self.plugin.pluginName + " caused the following exception:\n\n" + str(self.innerException))

class PluginLoadError(Exception):
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
    def __init__(self, pluginWrapper, procedure, eventName):
        self.pluginWrapper = pluginWrapper
        self.procedure = procedure
        self.eventName = eventName
        self.priority = Priorities.getPriority(procedure) #getattr(procedure, "priority", 3)

    def __call__(self, *args):
        try:
            return self.procedure(self.pluginWrapper.pluginObject, *args)
        except Exception as exception:
            logging.exception("The plugin %s raised an exception in the eventhandler %s.", self.pluginWrapper.pluginName, self.eventName)
            raise PluginExceptionError(self.pluginWrapper, exception)
            
    def __str__(self):
        return("%s handler for %s" % (self.eventName, self.pluginWrapper.pluginName))

#---------------------------------------------------------------------------------
#  PLUGIN
#---------------------------------------------------------------------------------
class PluginWrapper:
    """ Wraps a dynamically loaded plugin-class. """

    ## Creation and destruction
    def __init__(self, pluginInterface, filepath, enabled = True):
        self.pluginInterface = pluginInterface
        self.filepath = filepath
        self.enabled = enabled
        
        self.pluginName = self.filepath.stem
        self.module = None       # the module loaded from the python file
        self.pluginClass = None  # the class named self.pluginName defined in self.module
        self.pluginObject = None # an instance of the pluginClass
        
        self.handlers = []       # the event handlers that we register
        self.dependencies = {}   # dict of classname -> plugin
        self.dependents = set()  # set of PluginWrappers that have this plugin as a dependency
        self.dependenciesOnline = False
        
        self.pluginInterface.registerPlugin(self.pluginName, self)
        self.reload()
        
    def reload(self):
        self.disposePluginObject()
        if not self.filepath.exists():
            # This enters a weird state, ended when the pluginInterface
            # checks if this plugin has been updated and discovers that the file is missing.
            self.enabled = False
        try:
            self.loadPythonFile()
        except PluginLoadError:
            logging.exception("Error when loading plugin file %s", self.filepath)
            self.enabled = False
    
    def dispose(self):
        self.disposePluginObject()
        self.pluginInterface.unregisterPlugin(self.pluginName, self)
    
    def disposePluginObject(self):
        #if self.online():
        # DEBUG: CAN I ALWAYS CALL putOffline()? Because online() will never be true during a reload...
        self.putOffline()
            
        for wrapper in self.dependencies.values():
            wrapper.removeDependent(self)
        # remove the handlers from the wrapper
        self.handlers = []
        # remove module from sys.modules so that if/when the plugin is reloaded, 
        # it is not retrieved from the cache, but read from disk
        if self.module:
            del sys.modules[self.module.__name__]
        # if the plugin has a destructor, call it
        if self.pluginObject:
            try:
                self.pluginObject.dispose()
            except:
                pass
        self.pluginObject = None

    ##  Messages from the plugin interface
    def checkForUpdate(self):
        """Checks if there are any updates available for this plugin. Returns True if there were.
        Raises an exception if the file no longer exists"""
        if self.filepath.mtime != self.lastModified: # This line raises the exception
            self.enabled = True
            self.dependenciesOnline = False
            self.reload()
            return True

    def notifyDependencyChange(self, changes):
        """Called by the PluginInterface to inform us of when one of our dependencies have changed. 
        changes is a dictionary of pluginName --> PluginWrapper"""
        self.dependencies.update(changes)
        for plugin in changes.values():
            plugin.addDependent(self)
        self.notifyDependencyStateChange()  # since our dependencies changed, see if they are online.
        
    ##  Plugin state management

    @decorator
    def changesState(func, self, *args, **kwargs):
        """Decorator for methods that potentially change the plugin's state. Ensures that the plugin is
        taken online or offline accordingly"""
        stateBefore = self.online()
        func(self, *args, **kwargs)
        stateAfter = self.online()
        if stateBefore != stateAfter:
            if stateAfter:          
                self.putOnline()
            else:
                self.putOffline()
    
    def online(self):
        return self.dependenciesOnline and self.enabled
    
    def getStatus(self):
        if self.pluginObject and hasattr(self.pluginObject, "getVersionInformation"):
            version = self.pluginObject.getVersionInformation().split()
            revision = version[2]
            commit = version[3] + " " + version[4]
            creator = version[5]
        else:
            revision = "unknown"
            commit = "unknown"
            creator = "unknown"
        if self.online():
            status = "running"
        else:
            status = "offline"
        return (self.pluginName, status, revision, commit, creator)
    
    @changesState
    def setState(self, newState):
        "Sets whether the plugin is enabled or not"
        self.enabled = newState
    
    @changesState
    def notifyDependencyStateChange(self):
        "Checks if our dependencies are online. Called by our dependencies when they change their state"
        something1 = [plugin.online() for plugin in self.dependencies.values()]
        something2 = functools.reduce(operator.__and__, something1, True)
        self.dependenciesOnline = something2

    ## INTERNAL METHODS
    def putOnline(self):
        "Brings the plugin online again"
        logging.info("Bringing plugin %s online" % self.pluginName)
        if not self.pluginObject:
            self.instantiateObject()
        for handler in self.handlers:
            self.pluginInterface.registerEventHandler(handler)  
        for plugin in self.dependents:
            plugin.notifyDependencyStateChange()
            
    def putOffline(self):
        "Deactivates the plugin"
        logging.info("Bringing plugin %s offline" % self.pluginName)
        for handler in self.handlers:
            self.pluginInterface.unregisterEventHandler(handler)
        for plugin in self.dependents:
            plugin.notifyDependencyStateChange()

    def addDependent(self, plugin):
        self.dependents.add(plugin)
    def removeDependent(self, plugin):
        self.dependents.remove(plugin)
    def hasDependency(self, name):
        return name in self.dependencies.keys() or functools.reduce(operator.__or__, [dependency.hasDependency(name) for dependency in self.dependencies.values()], False)
    def getDependencies(self):
        return self.dependencies.keys()

    ## Pickling helper methods (serialization)
    def __getstate__(self):
        """Called by the pickle module for serialization"""
        # pick the fields that are suitable for serialization
        state = {"enabled": self.enabled, "pluginInterface": self.pluginInterface, "filepath": self.filepath}
        return state
    
    def __setstate__(self, dict):
        """Called by the pickle module for deserialization"""
        PluginWrapper.__init__(self, **dict)

    ## PARSING OF PY-FILE

    def loadPythonFile(self):
        """ Dynamically loads the plugin py-file, but does not instantiate the pluginObject """
        self.lastModified = self.filepath.stat().st_mtime
        try:
            self.module = importlib.import_module('plugins.' + self.filepath.stem)
        except Exception as e:
            logging.exception("Plugin raised exception during load")
            raise PluginLoadError(e) from e
        
        try:
            self.pluginClass = getattr(self.module, self.pluginName)
            assert inspect.isclass(self.pluginClass)
        except Exception as e:
            raise PluginLoadError("Can't find plugin class in file %s" % self.filepath.name) from e
        
        try:
            dependencyNames = set(self.pluginClass.getDependencies())                
        except (AttributeError, TypeError):  # if this fails ...
            dependencyNames = set() # then it's okay, it just means the plugin doesn't declare any dependencies, or that it doesn't declare getDependencies() as a classmethod
        except Exception as e:
            logging.exception("Plugin raised exception while trying to determine its dependencies")
            raise PluginLoadError(e) from e
        
        # Find all the event handlers
        for (name,funcobj) in self.pluginClass.__dict__.items():
            if name[:2] == "on" and callable(funcobj) :
                handler = EventHandler(self, funcobj, name)
                self.handlers.append(handler)
        logging.debug("Found %i event handlers for plugin %s" % (len(self.handlers), self.pluginName))        
        
        something1 = [self.pluginInterface.handleDependency(dep) for dep in dependencyNames]
        something2 = zip( dependencyNames, something1)
        something3 = dict( something2 )
        self.notifyDependencyChange( something3 )
        if self.hasDependency(self.pluginName):
            raise PluginLoadError("Circular dependency error in %s" % (self.pluginName,))

    def instantiateObject(self):
        try:
            #   if a constructor exists and it has two parameters (self, pluginInterface), call it with the pluginInterface as argument
            #if  hasattr(self.pluginClass,"__init__") and len(inspect.getargspec(self.pluginClass.__init__)[0]) == 2:
            #    self.pluginObject = self.pluginClass(self.pluginInterface)
            #else:  #   otherwise, call the argument-less constructor
            self.pluginObject = self.pluginClass()
            self.pluginObject.plugin_context = self.pluginInterface.pluginContext   # TODO: This gets injected instead of passed to the constructor, so that plugins don't have to remember
                                                                                    # to have it in their signature and pass it through. But I'm not sure whether this is really any better...
        except Exception as e:
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
        self.handlers.sort(key=functools.cmp_to_key(self.compareHandlers))

    async def fireEvent(self, *args):
        logging.debug("firing event")
        for procedure in self.handlers:
            logging.debug("firing event %s for plugin %s", procedure.eventName, procedure.pluginWrapper.pluginName)
            # event handler procedures return true to abort processing
            if await procedure(*args):
                break

#---------------------------------------------------------------------------------
#  PLUGIN INTERFACE
#    The main class of the plugin interface.
#---------------------------------------------------------------------------------
class PluginInterface:
#---------------------------------------------------------------------------------
#      PluginInterface Public interface
#---------------------------------------------------------------------------------
    pluginMetaData = Path("resources/PluginMetaData.pickle")
    def __init__(self, pluginsDirectory):
        self.pluginsDirectory = Path(pluginsDirectory)
        if not self.pluginsDirectory.exists():
            raise Exception("The plugins directory: " + pluginsDirectory + " doesn't exist!")        
        
        self.botcore = None
        self.eventHandlers = {}     # dict of eventName -> EventHandlerRepository
        self.pluginWrappers = {}    # dict of pluginName -> PluginWrapper
        if self.pluginMetaData.exists():
            try:
                up = pickle.Unpickler(self.pluginMetaData.open("r"))
                up.persistent_load = self.persistent_load
                up.load()
            except:
                pass # If we can't load the plugin states, no biggie...

        self.pluginContext = None   # FIXME: we're gonna inject this later, but of course that's not the right way to do this
        
    def dispose(self):
        p = pickle.Pickler(self.pluginMetaData.open("w"))
        p.persistent_id = self.persistent_id
        p.dump(self.pluginWrappers)

    def registerInformTarget(self, botcore):
        self.botcore = botcore

    async def fireEvent(self, eventname, *args):
        if eventname in self.eventHandlers:
            try:
                await self.eventHandlers[eventname].fireEvent(*args)
            except PluginExceptionError as exception:
                pluginName = exception.pluginWrapper.pluginName
                logging.info("Disabling erraneous plugin: %s", pluginName)
                if self.botcore:
                    self.botcore.informErrorRemovedPlugin("The plugin %s raised errors and is now disabled" % (pluginName))
                exception.pluginWrapper.setState(False)

    def updatePlugins(self, shallNotify=True):
        """ Searches for new, updated and removed plugins 
        shallNotify - true if the informTarget / botcore should be notified about
                      the changes. Used by BotManager during startup to avoid flooding the channel with changes"""
        logging.debug("Starting to update plugins")
        pluginsBefore = set(self.pluginWrappers.keys())  # for aggregating statistics. Keeps track of what plugins were before we make changes
        reloadedPlugins = set()
        # iterate over all our plugins and see if there are any changes
        for pluginName, pluginWrapper in self.pluginWrappers.items():
            try:
                if pluginWrapper.checkForUpdate() : # if there was an update...
                    logging.info("reloaded the plugin %s", pluginName)
                    reloadedPlugins.add(pluginName)
            except OSError as e:
                # file was not found
                self.pluginWrappers[pluginName].dispose()
                logging.info("The plugin %s was deleted", pluginName)
        # Check if there are any new files
        for file in self.pluginsDirectory.glob("*Plugin.py"):
            if not file.stem in self.pluginWrappers.keys():
                logging.info("New plugin file found: %s", file.name)
                PluginWrapper(self, file)
                if not self.pluginWrappers[file.stem].enabled:
                    self.botcore.informRemovedPluginDuringLoad("The plugin %s raised errors during load time and is now disabled" % (file.stem))

        pluginsAfter = set(self.pluginWrappers.keys())
        loadedPlugins = pluginsAfter.difference(pluginsBefore)
        removedPlugins = pluginsBefore.difference(pluginsAfter)
        # notify the botcore if requested
        if(shallNotify):
            if(self.botcore):
                self.botcore.informPluginChanges(loadedPlugins, reloadedPlugins, removedPlugins, [])
            else:
                raise Exception("ERROR: botcore isn't loaded yet, so I can't inform anyone of that failed plugin!")

    def setPluginState(self, pluginName, newState):
        """Changes the state of a plugin. If state is true, then the plugin
         will be enabled and process events if all its dependencies are available
        Raises KeyError if the plugin is not found"""
        if newState:
            logging.info("Activating plugin %s", pluginName)
        else:
            logging.info("Deactivating plugin %s", pluginName)      
        self.pluginWrappers[pluginName].setState(newState)

    def getPlugin(self, classname):
        """Returns an instance of a plugin class, given the name of the class.
        Returns None if the plugin can't be found or is offline"""
        if classname in self.pluginWrappers and self.pluginWrappers[classname].online():
            return self.pluginWrappers[classname].pluginObject
        else:
            # Originally intended to raise exception here, since plugins shouldn't
            # ever get execution time when dependencies are down. But versionplugin
            # foiled that idea.
            #raise MissingDependenciesError("Some plugin has an undeclared dependency to '%s', which is currently unavailable" % (classname,))
            return None

    def getPluginWrapper(self, classname):
        " Returns the pluginWrapper that wraps the specified plugin. Raises KeyError otherwise "
        return self.pluginWrappers[classname]

    def handleDependency(self, pluginName):
        return self.pluginWrappers.get(pluginName, MissingDependency(pluginName))

    def getPluginNames(self):
        """ Returns a list of names of all loaded plugins """
        return self.pluginWrappers.keys()

    def getPlugins(self):
        """ Returns a list of instances of all loaded plugins """
        return [wrapper.pluginObject for wrapper in self.pluginWrappers.values() if wrapper.online()]
    
    def getStatus(self):
        return [wrapper.getStatus() for wrapper in self.pluginWrappers.values() ]
           
#---------------------------------------------------------------------------------
#      PluginInterface module-internal methods
#---------------------------------------------------------------------------------  
    def registerEventHandler(self, handler):
        logging.info("Registering event %s for plugin %s" % (handler.eventName, handler.pluginWrapper.pluginName))
        if not handler.eventName in self.eventHandlers:
            self.eventHandlers[handler.eventName] = EventHandlerRepository()
        self.eventHandlers[handler.eventName].addHandler(handler)
    def unregisterEventHandler(self, handler):
        logging.info("Unregistering event %s for plugin %s" % (handler.eventName, handler.pluginWrapper.pluginName))
        self.eventHandlers[handler.eventName].removeHandler(handler)
        
    def registerPlugin(self, pluginName, pluginWrapper):
        logging.info("Registering the plugin %s" % pluginName)
        if pluginName in self.pluginWrappers.keys():
            raise Exception("Tried to Register the same plugin twice")
        changes = { pluginName : pluginWrapper }
        for wrapper in self.pluginWrappers.values():
            if wrapper.hasDependency(pluginName):
                wrapper.notifyDependencyChange(changes)
        self.pluginWrappers[pluginName] = pluginWrapper  

    def unregisterPlugin(self, pluginName, pluginWrapper):
        logging.debug("Unregistering the plugin %s" % pluginName)
        del self.pluginWrappers[pluginName]
        changes = { pluginName : MissingDependency(pluginName) }
        for p in self.pluginWrappers.values():        # Technically, the PluginWrapper could do this by itself,
            if p.hasDependency(pluginWrapper.pluginName):    # but this way seems more symmetrical
                p.notifyDependencyChange(changes)
                
    # Helper methods for pickling
    def persistent_id(self, obj):
        if isinstance(obj, PluginInterface):
            return "MyPersistentID"
    def persistent_load(self, persid):
        if persid == "MyPersistentID":
            return self
