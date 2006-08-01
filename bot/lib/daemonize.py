"""
    This module is used to fork the current process into a daemon.
    Almost none of this is necessary (or advisable) if your daemon 
    is being started by inetd. In that case, stdin, stdout and stderr are 
    all set up for you to refer to the network connection, and the fork()s 
    and session manipulation should not be done (to avoid confusing inetd). 
    Only the chdir() and umask() steps remain as useful.
    References:
        UNIX Programming FAQ
            1.7 How do I get my program to act like a daemon?
                http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        Advanced Programming in the Unix Environment
            W. Richard Stevens, 1992, Addison-Wesley, ISBN 0-201-56317-7.

    History:
      2001/07/10 by Juergen Hermann
      2002/08/28 by Noah Spurrier
      2003/02/24 by Clark Evans
      
      http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66012
"""

# A daemon process is usually defined as a background process that does not belong to a terminal session. Many
# system services are performed by daemons; network services, printing etc.

# Simply invoking a program in the background isn't really adequate for these long-running programs; that does
# not correctly detach the process from the terminal session that started it. Also, the conventional way of
# starting daemons is simply to issue the command manually or from an rc script; the daemon is expected to put
# itself into the background.

# Here are the steps to become a daemon:

#   1. fork() so the parent can exit, this returns control to the command line or shell invoking your program.
#      This step is required so that the new process is guaranteed not to be a process group leader. The next
#      step, setsid(), fails if you're a process group leader.
#   2. setsid() to become a process group and session group leader. Since a controlling terminal is associated
#      with a session, and this new session has not yet acquired a controlling terminal our process now has no
#      controlling terminal, which is a Good Thing for daemons.
#   3. fork() again so the parent, (the session group leader), can exit. This means that we, as a non-session
#      group leader, can never regain a controlling terminal.
#   4. chdir("/") to ensure that our process doesn't keep any directory in use. Failure to do this could make
#      it so that an administrator couldn't unmount a filesystem, because it was our current directory.
#      [Equivalently, we could change to any directory containing files important to the daemon's operation.]
#   5. umask(0) so that we have complete control over the permissions of anything we write. We don't know what
#      umask we may have inherited. [This step is optional]
#   6. close() fds 0, 1, and 2. This releases the standard in, out, and error we inherited from our parent
#      process. We have no way of knowing where these fds might have been redirected to. Note that many daemons
#      use sysconf() to determine the limit _SC_OPEN_MAX. _SC_OPEN_MAX tells you the maximun open files/process.
#      Then in a loop, the daemon can close all possible file descriptors. You have to decide if you need to do
#      this or not. If you think that there might be file-descriptors open you should close them, since there's
#      a limit on number of concurrent file descriptors.
#   7. Establish new open descriptors for stdin, stdout and stderr. Even if you don't plan to use them, it is
#      still a good idea to have them open. The precise handling of these is a matter of taste; if you have a
#      logfile, for example, you might wish to open it as stdout or stderr, and open `/dev/null' as stdin;
#      alternatively, you could open `/dev/console' as stderr and/or stdout, and `/dev/null' as stdin, or any
#      other combination that makes sense for your particular daemon. 

import os, sys, time, signal

usedSignal = signal.SIGTERM

def signalHandler(signum, frame):
    print 'Signal handler called with signal', signum
    raise KeyboardInterrupt, "SIGNAL received!"

def deamonize(stdout='/dev/null', stderr='/dev/null', stdin='/dev/null',
              pidfile=None, startmsg = 'started with pid %s' ):
    """
        This forks the current process into a daemon.
        The stdin, stdout, and stderr arguments are file names that
        will be opened and be used to replace the standard file descriptors
        in sys.stdin, sys.stdout, and sys.stderr.
        These arguments are optional and default to /dev/null.
        Note that stderr is opened unbuffered, so
        if it shares a file with stdout then interleaved output
        may not appear in the order that you expect.
    """
    
    # set a handler for signal
    signal.signal(usedSignal, signalHandler)

    # Do first fork.
    try: 
        pid = os.fork() 
        if pid > 0: sys.exit(0) # Exit first parent.
        print "fork #1 succeeded"
    except OSError, e: 
        print "fork #1 failed: (%d) %s\n" % (e.errno, e.strerror)
        sys.stderr.write("fork #1 failed: (%d) %s\n" % (e.errno, e.strerror))
        sys.exit(1)

    # Decouple from parent environment.
    #os.chdir("/") 
    os.umask(0) 
    os.setsid()
    
    # Do second fork.
    try: 
        pid = os.fork() 
        print "fork #2 succeeded"
        if pid > 0: sys.exit(0) # Exit second parent.
    except OSError, e: 
        print "fork #2 failed: (%d) %s\n" % (e.errno, e.strerror)
        sys.stderr.write("fork #2 failed: (%d) %s\n" % (e.errno, e.strerror))
        sys.exit(1)
    
    # Open file descriptors and print start message
    if not stderr: stderr = stdout
    si = file(stdin, 'r')
    so = file(stdout, 'a+')
    se = file(stderr, 'a+', 0)
    pid = str(os.getpid())
    sys.stderr.write("\n%s\n" % startmsg % pid)
    sys.stderr.flush()
    if pidfile: file(pidfile,'w+').write("%s\n" % pid)
    print "opened file descriptors"
    
    # Redirect standard file descriptors.
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())



def startstop(stdout='/dev/null', stderr=None, stdin='/dev/null',
              pidfile='pid.txt', startmsg = 'started with pid %s' ):
    # print usage if no argument has been supplied
    if len(sys.argv) > 1:
        # detect the action
        action = sys.argv[1]
        print "action: %s" % (action)
        
        # read the PID
        try:
            pf  = file(pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
            print "Found the pid: %i" % (pid)
        except IOError:
            pid = None
            print "pid not found, not necessarily an error."

        # STOP / RESTART
        if 'stop' == action or 'restart' == action:
            # error message if no PID
            if not pid:
                mess = "Could not stop, pid file '%s' missing.\n"
                sys.stderr.write(mess % pidfile)
                sys.exit(1)

            # try to kill the old process until it's dead
            print "Trying to kill the old process and then waiting until it's gone."
            try:
                os.kill(pid, usedSignal)
                while 1:
                   os.kill(pid, signal.SIGCONT)
                   time.sleep(1)

            # this is not an exception, it's the expected case that the process is gone
            except OSError, err:
               print "The process is gone now."
               err = str(err)
               if err.find("No such process") > 0:
                   print "Couldn't find the process, this is expected and not an error."
                   # delete the pid file
                   os.remove(pidfile)
                   # if STOP, then we're done here
                   if 'stop' == action:
                       sys.exit(0)
                   # if RESTART, we need to do the START-stuff now
                   action = 'start'
                   print "new action: %s" % (action)
                   pid = None
               else:
                   print "Found process, this is an error, exiting."
                   print str(err)
                   sys.exit(1)
        if 'start' == action:
            print "Starting to handle the 'start' action."
            if pid:
                mess = "Start aborded since pid file '%s' exists.\n"
                print mess % pidfile
                sys.stderr.write(mess % pidfile)
                sys.exit(1)
            # run daemonize()
            print "Running daemonize()..."
            deamonize(stdout,stderr,stdin,pidfile,startmsg)
            print "Ran daemonize()."
            return
    print "usage: %s start|stop|restart" % sys.argv[0]
    sys.exit(2)