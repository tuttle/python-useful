from functools import wraps
import os
import time
import errno

# Based on http://www.evanfosmark.com/2009/01/cross-platform-file-locking-support-in-python/


class FileLockTimeoutException(Exception):
    pass


class FileLock(object):
    """ A file locking mechanism that has context-manager support so
        you can use it in a with statement. This should be relatively cross
        compatible as it doesn't rely on msvcrt or fcntl for the locking.
        Timeout when waiting for lock is supported.

        WARNING: The code is not safe for all NFS implementations.

        See the O_EXCL section of the "open" manpage, test it first!

        Usage example::

            with FileLock('/tmp/myproject-critical-processing'):
                print "This section will only be executed by a single thread at the same time."

        You can also use the instance as the decorator::

            @FileLock('/tmp/func1-critical-processing')
            def func1():
                print "This function will only be executed by a single thread at the same time."

        Also the lock stealing is implemented (stealing=True), but only on the POSIX system where it is possible to send
        signal 0 to process to test its existence. If requested, the locking process will write a small JSON info to the
        lockfile. Each time before waiting for lock to be released, the competing process signals the lock originator
        by PID. If the locking process does not exist, the lock file is removed and acquiring is tried again.
    """
    def __init__(self, file_name, timeout=30, delay=0.2, stealing=False):
        """ Prepare the file locker. Specify the file to lock and optionally
            the maximum timeout and the delay between each attempt to lock.
        """
        self.is_locked = False
        self.lockfile = os.path.join(os.getcwd(), "%s.lock" % file_name)
        self.file_name = file_name
        self.timeout = timeout
        self.delay = delay
        self.stealing = stealing

        if stealing:
            if os.name != 'posix':
                raise RuntimeError("Detecting a running process by its PID is only supported on a POSIX system.")

            import json
            self.json = json

    def acquire(self):
        """ Acquire the lock, if possible. If the lock is in use, it check again
            every `wait` seconds. It does this until it either gets the lock or
            exceeds `timeout` number of seconds, in which case it throws
            an exception.
        """
        start_time = time.time()
        while True:
            try:
                self.fd = os.open(self.lockfile, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                break
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise

                if self.should_steal():
                    os.unlink(self.lockfile)
                    continue

                if (time.time() - start_time) >= self.timeout:
                    raise FileLockTimeoutException("%d seconds passed." % self.timeout)

                time.sleep(self.delay)

        self.is_locked = True

        if self.stealing:
            import datetime
            import sys

            info = {
                'lock_time': datetime.datetime.now().isoformat(),  # warning: timezone unaware!
                'pid': os.getpid(),
                'argv': sys.argv,
            }
            os.write(self.fd, self.json.dumps(info, indent=4))
            os.fsync(self.fd)

    def release(self):
        """ Get rid of the lock by deleting the lockfile.
            When working in a `with` statement, this gets automatically
            called at the end.
        """
        if self.is_locked:
            os.close(self.fd)
            os.unlink(self.lockfile)
            self.is_locked = False

    def should_steal(self):
        if self.stealing:
            try:
                info = self.json.load(open(self.lockfile))
            except ValueError:
                # We don't steal if the lockfile is empty of contains an invalid JSON value.
                pass
            else:
                try:
                    # POSIX test whether the given PID exists
                    os.kill(info['pid'], 0)
                except OSError as e:
                    # For EPERM we intentionally don't steal as the locking process might have higher privilege.
                    # ESRCH means "No such process".
                    if e.errno == errno.ESRCH:
                        return True

        return False

    def __enter__(self):
        """ Activated when used in the with statement.
            Should automatically acquire a lock to be used in the with block.
        """
        if not self.is_locked:
            self.acquire()
        return self

    def __exit__(self, exc_type, exc_value, traceback):  # @UnusedVariable
        """ Activated at the end of the with statement.
            It automatically releases the lock if it isn't locked.
        """
        if self.is_locked:
            self.release()

    def __del__(self):
        """ Make sure that the FileLock instance doesn't leave a lockfile
            lying around.
        """
        self.release()

    def __call__(self, function):
        """
        Support for using the instance as decorator. The entire function will be protected.
        """
        @wraps(function)
        def inner(*args, **kwargs):
            with self:
                return function(*args, **kwargs)

        return inner
