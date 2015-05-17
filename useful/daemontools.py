import os
import sys
import pwd
import grp
import logging.handlers
import signal
import atexit

# For becoming the daemon django.utils.daemonize.become_daemon() is used.
# The additional daemon-stuff utilities follow:


def drop_privileges(user='nobody', group='nogroup'):
    """
    Drop privileges if we're superuser by changing UID/GID to given user/group.
    """
    if os.geteuid() == 0:
        # Remove group privileges
        os.setgroups([])

        if group != 'root':
            try:
                newgid = grp.getgrnam(group).gr_gid
            except KeyError:
                raise RuntimeError("System group '%s' not found." % group)

            os.setgid(newgid)
            os.setegid(newgid)

        if user != 'root':
            try:
                newuid = pwd.getpwnam(user).pw_uid
            except KeyError:
                raise RuntimeError("System user '%s' not found." % user)

            os.setuid(newuid)
            os.seteuid(newuid)


def install_termination_logging_signal_handlers():
    """
    Install the handler for every reconfigurable signal (except some
    ignorables). On signal, the event is logged and process is terminated.
    """
    def sig_handler(signum, unused_frame):
        signames = [n for n, v in signal.__dict__.iteritems()
                    if n.startswith('SIG') and v == signum]
        signame = signames and ' (%s)' % signames[0] or ''
        logging.info("Terminating with signal %d%s." % (signum, signame))
        sys.exit(2)     # calls exit_function

    for s in xrange(100):
        if s not in (signal.SIGCHLD, signal.SIGURG, signal.SIGWINCH):
            try:
                signal.signal(s, sig_handler)
            except:
                pass


def init_syslog(level, process_ident, address='/dev/log', facility='daemon'):
    """
    Set the root logger to be directed to syslog from the given level
    and with given ident string (which will get prepended to every message).
    """
    logging.root.setLevel(level)
    if len(logging.root.handlers) == 0:
        fmt = '%s %%(levelname)s: %%(message)s' % process_ident
        hdlr = logging.handlers.SysLogHandler(address, facility)
        hdlr.setFormatter(logging.Formatter(fmt))
        logging.root.addHandler(hdlr)


def setup_pidfile(pidfile_path):
    """
    Fails if there is something at the given path. Otherwise, writes
    the current PID to file at that path. Also sets the atexit
    handler to automatically remove the file upon exit.

    Note: The process needs to have file removing privileges in the end.
    """
    def exit_function(pidfile_path):
        try:
            logging.debug("Removing PID file %s." % pidfile_path)
            os.unlink(pidfile_path)
        except:
            logging.error("Cannot remove PID file %s." % pidfile_path)

    if os.path.exists(pidfile_path):
        logging.error("Pid file %s exists, aborting daemonization. "
                      "Please assure that I'm not already running." % pidfile_path)
        sys.exit(3)

    atexit.register(exit_function, pidfile_path)
    open(pidfile_path, 'w').write('%d\n' % os.getpid())
