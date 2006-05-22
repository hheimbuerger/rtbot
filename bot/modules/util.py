# Decorator for decorators that don't take any arguments - http://miscoranda.com/134

def decorator(decorfunc): 
   def wrapper(func): 
      return lambda *args, **kwargs: decorfunc(func, *args, **kwargs)
   return wrapper

# Decorator for functions that need to acquire a lock before executing.
# if block is true, the function blocks until the lock is available
# if block is false, the function tries to acquire the lock immediately.
#                   if this fails, the function does nothing

def withLock(lock, blocking = True):
    def decorator(func):
        def wrapped(*args, **kwargs):
            if not lock.acquire(blocking):
                return
            func(*args, **kwargs)
            lock.release()
        return wrapped
    return decorator

# Same as above, but for a class member where the lock is stored in the
# class instance. A bit awkward, but decorators are executed when the *class*
# is created, not when the instance is created. Therefore, there is no self,
# and no instance-specific lock until later.

# lockName should be the name of the lock variable
def withMemberLock(lockName, blocking = True):
    def decorator(func):
        def wrapped(self, *args, **kwargs):
            lock = self.__dict__[lockName]
            if not lock.acquire(blocking):
                return
            func(self, *args, **kwargs)
            lock.release()
        return wrapped
    return decorator

from UserDict import UserDict
import pickle
class Archive(UserDict):
    # This is basically a shelf with custom picklers
    def __init__(self, filepath, persistent_id, persistent_load):
        self.__dict__.update(locals())
        if filepath.exists() and not filepath.size == 0:
            up = pickle.Unpickler(filepath.open("rb"))
            up.persistent_load = self.persistent_load
            try:
                data = up.load()
            except:
                data = {}
        else:
            data = {}
        UserDict.__init__(self, data)
    def __del__(self):
        self.sync()
    def sync(self):
        "Writes the contents of the data back to disk"
        p = pickle.Pickler(self.filepath.open("wb"), -1) # use highest version of pickle protocol
        p.persistent_id = self.persistent_id
        p.dump(self.data)
    def __setitem__(self, key, item):
        self.data[key] = item
        self.sync()
    def __delitem__(self, key):
        del self.data[key]
        self.sync()