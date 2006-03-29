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