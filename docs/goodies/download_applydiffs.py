#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# This script downloads and applies any and all imdb diff files which
# have not already been applied to the lists in the ImdbListsPath folder
#
# NOTE: this is especially useful in Windows environment; you have
# to modify the paths in the 'Script configuration' section below,
# accordingly with your needs.
#
# The script makes the assumption that the ImdbDiffsPath folder contains
# the diff file which was most recently applied to the imdb lists. If that
# folder contains no imdb diff files then the script will use the value of
# imdbListsDownloadDate as a baseline to determine which diff files to
# download and apply
#
# If a downloaded imdb diff file cannot be applied correctly then this script
# will fail as gracefully as possible
#
# Copyright 2013 (C) Roy Stead
# Released under the terms of the GPL license.
#

import os


#############################################
#           Script configuration            #
#############################################

# The local folder where imdb list and diffs files are stored
ImdbListsPath = "Z:\\MovieDB\\data\\lists"
ImdbDiffsPath = os.path.join(ImdbListsPath,"diffs")

# Define the system commands to unZip, unTar, Patch and Gzip a file
# Values are substituted into these template strings at runtime, in the order indicated
#
# Note that the code REQUIRES that the program used to apply patches MUST return 0 on success and non-zero on failure
#
unGzip="\"C:/Program Files/7-Zip/7z.exe\" e %s -o%s"                                # params = archive, destination folder
unTar=unGzip                                                                        # params = archive, destination folder
applyPatch="\"Z:/MovieDB/Scripts/patch.exe\" --binary --force --silent %s %s"       # params = listfile, diffsfile
progGZip="\"Z:/MovieDB/Scripts/gzip.exe\" %s"                                       # param = file to Gzip

# Specify a program to be run after a successful update of the imdb lists
# Set to None if no such program should be run
RunAfterSuccessfulUpdate="\"Z:\\MovieDB\\Scripts\\Update db from imdb lists.bat\""


# The date that the imdb lists were originally downloaded
# Date format is "%Y-%m-%d" ("yyyy-mm-dd")
#
# If no diffs files are present in ImdbDiffsPath then all diffs
# from this date onwards will be downloaded and applied if possible
#
# A more robust approach here would be to have the script examine the
# first line (or last-modified date) of all the imdb list files and
# then set THIS value itself to the most recent date found (doing that
# only in the case where the ImdbDiffsPath folder is empty of course)
imdbListsDownloadDate = "2013-01-13"


# Possible FTP servers for downloading imdb diff files and the path to the diff files on each server
ImdbDiffsFtpServers = [ \
    {'url': "ftp.fu-berlin.de", 'path': "/pub/misc/movies/database/diffs"}, \
#    {'url': "ftp.sunet.se", 'path': "/pub/tv+movies/imdb/diffs"}, \                # Swedish server isn't kept up to date
    {'url': "ftp.funet.fi", 'path': "/pub/mirrors/ftp.imdb.com/pub/diffs"} ]


#############################################
#                Script Code                #
#############################################

# System and database libs
import subprocess
import sys
import shutil
import re
import datetime
import time

from datetime import timedelta,datetime
from ftplib import FTP
from random import choice


# Returns 1 if the supplied filename is a file in ImdbDiffsPath of the correct format for being an imdb diffs file
def isDiffFile(f):
    if re.match("diffs\-[0-9][0-9][0-9][0-9][0-9][0-9]\.tar\.gz", f):
        if os.path.isfile(os.path.join(ImdbDiffsPath, f)):
            return 1
    return 0


# Delete all files and subfolders in the specified folder and the folder itself
def deleteFolder(folder):
    if os.path.isdir(folder):
        shutil.rmtree(folder)


# Downloads and applies all imdb diff files which have not yet been applied to the current imdb lists
def applyDiffs():

    # Get list of downloaded (and presumably already applied) imdb diff files
    diffsApplied = [f for f in os.listdir(ImdbDiffsPath) if isDiffFile(f)]

    # Get the date of the most recent Friday (i.e. the most recently released imdb diffs)
    # Note Saturday and Sunday are a special case since Python's day of the week numbering starts at Monday = 0
    day = datetime.now()
    day.replace(hour=0, minute=0, second=0)
    if day.weekday() >= 4:
        mostrecentfriday =  day - timedelta(days=day.weekday()) + timedelta(days=4, weeks=-1)   # Fri/Sat/Sun = 4, 5, 6
    else:
        mostrecentfriday =  day - timedelta(days=day.weekday()) + timedelta(days=4, weeks=-2)   # The rest of the day = 0 to 4


    if len(diffsApplied) == 0:

        # No diff files found, so check if we know the date that the
        # imdb list files were originally downloaded
        if imdbListsDownloadDate:
            day = datetime.strptime(imdbListsDownloadDate,"%Y-%m-%d")
        else:
            print "No diffs files found in folder %s\n" \
                    "Unable to determine how up to date the imdb lists are.\n\n" \
                    "\tPlease set a value for imdbListsDownloadDate.\n" % ImdbDiffsPath
            return

        # Retrieve the date of the Friday before 'day',
        # which is the date stamp of the first imdb diffs to apply
        #
        # This assumes that if you downloaded the lists on a Friday then you downloaded a copy
        # which already had that day's diffs applied. If that is not the case then you'll need
        # to adjust the condition to read ">= 4" instead of just "> 4"
        if day.weekday() > 4:
            friday =  day - timedelta(days=day.weekday()) + timedelta(days=4, weeks=-1)
        else:
            friday =  day - timedelta(days=day.weekday()) + timedelta(days=4, weeks=-2)
    else:

        # Loop back in time until we find a matching (and presumed
        # to have already been applied) downloaded imdb diff file
        friday = mostrecentfriday
        while 1:
            diff = "diffs-%s.tar.gz" % friday.strftime("%y%m%d")
            if diff in diffsApplied:
                friday += timedelta(days=7);
                break
            friday -= timedelta(days=7);

    if friday > mostrecentfriday:
        print "imdb database is already up to date\n"
        return

    # At this point, we know we need to download and apply imdb diff files
    # so first step is to uncompress our existing list files to a folder so
    # we can apply diffs to them.
    tmpListsPath = os.path.join(ImdbDiffsPath,"lists")
    deleteFolder(tmpListsPath)
    os.mkdir(tmpListsPath)

    # Uncompress list files in ImdbListsPath to our temporary folder tmpListsPath
    numListFiles = 0;
    for f in os.listdir(ImdbListsPath):
        if re.match(".*\.list\.gz",f):
            try:
                cmdUnGzip = unGzip % (os.path.join(ImdbListsPath,f), tmpListsPath)
                subprocess.call(cmdUnGzip , shell=True)
            except Exception, e:
                print "Unable to uncompress imdb list file using: %s\n\t%e" % (cmdUnGzip, str(e))
            numListFiles++;

    if numListFiles == 0:
        print "No imdb list files found in %s." % ImdbListsPath
        return

    try:
        # Choose a random ftp server from which to download the imdb diff file(s)
        ImdbDiffsFtpServer = choice(ImdbDiffsFtpServers)
        ImdbDiffsFtp = ImdbDiffsFtpServer['url']
        ImdbDiffsFtpPath = ImdbDiffsFtpServer['path']

        # Connect to chosen imdb FTP server
        ftp = FTP(ImdbDiffsFtp)
        ftp.login()

        # Change to the diffs folder on the imdb files server
        ftp.cwd(ImdbDiffsFtpPath)
    except Exception, e:
        print str(e)
        return

    # Now go forwards in time from that point and for each imdb diff file we expect download and apply it
    patchedOKWith = None
    while 1:

        # Download the diffs file from the imdb files server
        diff = "diffs-%s.tar.gz" % friday.strftime("%y%m%d")
        diffFilePath = os.path.join(ImdbDiffsPath, diff)

        print "Downloading ftp://%s%s/%s" % ( ImdbDiffsFtp, ImdbDiffsFtpPath, diff )
        diffFile = open(diffFilePath, 'wb');
        try:
            ftp.retrbinary("RETR " + diff, diffFile.write)
            diffFile.close()
        except Exception, e:
            print "Unable to download %s:\n\t%s\n" % (diff, str(e))
            diffFile.close()
            os.remove(diffFilePath)
            return

        print "\tSuccessfully downloaded %s\n" % (diffFilePath)

        # Now uncompress the diffs file to a subdirectory.
        #
        # If that subdirectory already exists, delete any files from it
        # in case they are stale and replace them with files from the
        # newly-downloaded imdb diff file
        tmpDiffsPath = os.path.join(ImdbDiffsPath,"diffs")
        deleteFolder(tmpDiffsPath)
        os.mkdir(tmpDiffsPath)

        # unZip the diffs file to create a file diffs.tar
        try:
            cmdUnGzip = unGzip % (diffFilePath, tmpDiffsPath)
            subprocess.call(cmdUnGzip, shell=True)
        except Exception, e:
            print "Unable to unzip imdb diffs file using: %s\n\t%s" % (cmdUnGzip, str(e))
            return

        # unTar the file diffs.tar
        tarFile = os.path.join(tmpDiffsPath,"diffs.tar")
        patchStatus = 0
        if os.path.isfile(tarFile):
            try:
                cmdUnTar = unTar % (tarFile, tmpDiffsPath)
                subprocess.call(cmdUnTar, shell=True)
            except Exception, e:
                print "Unable to untar imdb diffs file using: %s\n\t%s" % (cmdUnTar, str(e))
                return

            # Clean up tar file and the sub-folder which 7z may have (weirdly) created while unTarring it
            os.remove(tarFile);
            if os.path.exists(os.path.join(tmpDiffsPath,"diffs")):
                os.rmdir(os.path.join(tmpDiffsPath,"diffs"));

            # Apply all the patch files to the list files in tmpListsPath
            isFirstPatchFile = True
            for f in os.listdir(tmpDiffsPath):
                if re.match(".*\.list",f):
                    print "Patching imdb list file %s\n" % f
                    try:
                        cmdApplyPatch = applyPatch % (os.path.join(tmpListsPath,f), os.path.join(tmpDiffsPath,f))
                        patchStatus = subprocess.call(cmdApplyPatch, shell=True)
                    except Exception, e:
                        print "Unable to patch imdb list file using: %s\n\t%s" % (cmdApplyPatch, str(e))
                        patchStatus=-1

                    if patchStatus <> 0:

                        # Patch failed so...
                        print "Patch status %s: Wrong diff file for these imdb lists (%s)\n" % (patchStatus, diff)

                        # Delete the erroneous imdb diff file
                        os.remove(diffFilePath)

                        # Clean up temporary diff files
                        deleteFolder(tmpDiffsPath)

                        if patchedOKWith <> None and isFirstPatchFile:

                            # The previous imdb diffs file succeeded and the current diffs file failed with the
                            # first attempted patch, so we can keep our updated list files up to this point
                            print "\tPatched OK up to and including imdb diff file %s ONLY\n" % patchedOKWith
                            break

                        else:
                            # We've not managed to successfully apply any imdb diff files and this was not the
                            # first patch attempt from a diff file from this imdb diffs file so we cannot rely
                            # on the updated imdb lists being accurate, in which case delete them and abandon
                            print "\tAbandoning update: original imdb lists are unchanged\n"
                            deleteFolder(tmpListsPath)
                            return

                    # Reset isFirstPatchFile flag since we have successfully
                    # applied at least one patch file from this imdb diffs file
                    isFirstPatchFile = False

        # Clean up the imdb diff files and their temporary folder
        deleteFolder(tmpDiffsPath)

        # Note the imdb patch file which was successfully applied, if any
        if patchStatus == 0:
            patchedOKWith = diff

        if friday == mostrecentfriday:
            break

        # We're not done, so go get the following week's imdb diff files
        friday += timedelta(days=7)

    # Close FTP connection
    ftp.close()

    # List files are all updated so re-Gzip them up and delete the old list files
    for f in os.listdir(tmpListsPath):
        if re.match(".*\.list",f):
            try:
                cmdGZip = progGZip % os.path.join(tmpListsPath,f)
                subprocess.call(cmdGZip, shell=True)
            except Exception, e:
                print "Unable to Gzip imdb list file using: %s\n\t%s" % (cmdGZip, str(e))
                break
            if os.path.isfile(os.path.join(tmpListsPath,f)):
                os.remove(os.path.join(tmpListsPath,f))

    # Now move the updated and compressed lists to the main lists folder, replacing the old list files
    for f in os.listdir(tmpListsPath):
        if re.match(".*\.list.gz",f):
            # Delete the original compressed list file from ImdbListsPath if it exists 
            if os.path.isfile(os.path.join(ImdbListsPath,f)):
                os.remove(os.path.join(ImdbListsPath,f))

            # Move the updated compressed list file to ImdbListsPath
            os.rename(os.path.join(tmpListsPath,f),os.path.join(ImdbListsPath,f))

    # Clean up the now-empty tmpListsPath temporary folder and anything left inside it
    deleteFolder(tmpListsPath)

    # If the imdb lists were successfully updated, even partially, then run my
    # DOS batch file "Update db from imdb lists.bat" to rebuild the imdbPy database
    # and relink and reintegrate my shadow tables data into it
    if patchedOKWith <> None:
        print "imdb lists are now updated up to imdb diffs file %s\n" % patchedOKWith
        if RunAfterSuccessfulUpdate <> None:
            subprocess.call(RunAfterSuccessfulUpdate, shell=True)

applyDiffs()
