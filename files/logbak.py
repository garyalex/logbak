#!/usr/bin/env python

import os
import re
import datetime
import shutil
import gzip
import argparse
from email.Utils import formatdate

# Setup our arguments
parser = argparse.ArgumentParser()
parser.add_argument('--debug', '-d',
                    action='store_true',
                    help='debug flag')
args = parser.parse_args()

# Set our variables from commandline arguments
debugflag = args.debug

# Constants
logfile = "/opt/logbak/reports/logbak.log"
levels = ('INFO', 'WARN', 'ERROR', 'DEBUG')


def logmessage(message, level):
    logtimestamp = formatdate()
    level = int(level)
    if debugflag:
        print(message)
    f = open(logfile, 'a')
    f.write('%s LOGBAK %s %s\n' % (logtimestamp, levels[level], message))
    f.close()
    return


def gzipfile(fullpath, modtime):
    logmessage("gzipping: %s %s" % (fullpath, modtime), 0)
    f_in = open(fullpath)
    f_out = gzip.open('%s.gz' % fullpath, 'wb')
    f_out.writelines(f_in)
    f_out.close()
    f_in.close()
    os.remove(fullpath)
    return


def mvfile(fullpath, modtime, filename, backdir):
    if backdir == "delete":
        logmessage("deleting: %s %s " % (fullpath, modtime), 0)
        os.remove(fullpath)
    else:
        destpath = os.path.join(backdir, filename)
        logmessage("moving: %s %s to %s" % (fullpath, modtime, destpath), 0)
        shutil.move(fullpath, destpath)
    return


# Get current time
now = datetime.datetime.now()

# Open logbak.conf to get directory list
file = open("/opt/logbak/logbak.conf", 'r')
content = file.read()
configfile = content.split("\n")

# loop over config lines in file
for configlines in configfile:
    # Remove whitespace from left and right of string
    configlines = configlines.strip(' \t\n\r')
    if configlines != "":
        logdir, backdir, logpattern, gzolder, mvolder = configlines.split(" ")
        infomsg = "Now backing up: %s to %s " % (logdir, backdir)
        infomsg += "with log pattern: [[%s]] " % logpattern
        infomsg += "policy: zip older than %s days " % gzolder
        infomsg += "policy: move older than %s days" % mvolder
        logmessage(infomsg, 0)
        # Compile regexes based on pattern
        regexgzip = re.compile("%s$" % logpattern)
        regexmv = re.compile("%s\.gz$" % logpattern)
        # get our datetimes for each type of filename
        gztime = now - datetime.timedelta(days=int(gzolder))
        mvtime = now - datetime.timedelta(days=int(mvolder))
        # Get our filelist to run actions
        for filename in os.listdir(logdir):
            # Get full path name and mtime
            fullpath = os.path.join(logdir, filename)
            timestamp = os.path.getmtime(fullpath)
            modtime = datetime.datetime.fromtimestamp(timestamp)

            # Check if file matches regex to gzip and mod time
            if regexgzip.search(filename) and gztime > modtime and os.path.isfile(fullpath):
                gzipfile(fullpath, modtime)
            # Check if file matches regex to mv and mod time
            elif regexmv.search(filename) and mvtime > modtime and os.path.isfile(fullpath):
                mvfile(fullpath, modtime, filename, backdir)
