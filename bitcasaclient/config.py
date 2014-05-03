#   Copyright 2014 Derrick J. Wippler
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from __future__ import print_function
from ConfigParser import NoSectionError, NoOptionError, DuplicateSectionError
import ConfigParser
import os


class SafeConfigParser(ConfigParser.RawConfigParser):
    """ Simple subclass to add the safeGet() method """
    def getError(self):
        return None

    def safeGet(self, section, key):
        try:
            return ConfigParser.RawConfigParser.get(self, section, key)
        except (NoSectionError, NoOptionError):
            return None


def openFd(file):
    """ Open the file if possible, else return None """
    try:
        return open(file)
    except IOError:
        return None


def extract_config(client):
    return {
        'client-id': client.id,
        'secret': client.secret,
        'redirect-url': client.redirect_url,
        'access-token': client.access_token
    }


def writeDict(fileName, conf):
    fileName = os.path.expanduser(fileName)
    print("-- Writing: %s" % fileName)
    with open(fileName, 'w') as fd:
        fd.write('[bitcasa]\n')
        for key, value in conf.items():
            fd.write("%s=%s\n" % (key, value))


def writeTokenFile(fileName, client):
    writeDict(fileName, {'access-token': client.access_token})


def readTokenFile(file):
    try:
        return dict(readConfig(file).items('bitcasa'))['access-token']
    except RuntimeError:
        return None


def saveConfig(config, fileName):
    fileName = os.path.expanduser(fileName)
    with open(fileName, 'w') as fd:
        config.write(fd)


def saveCompleted(conf, downloadDir, completed, fileName):
    """ Save a listing of the file already downloaded for this directory """
    try:
        # No need to save an empty list
        if len(completed) == 0:
            return
        conf.add_section(downloadDir)
    except DuplicateSectionError:
        pass

    for key, value in completed.items():
        conf.set(downloadDir, key, value)
    # Write the config
    saveConfig(conf, fileName)


def readConfig(file):
    """ Given a list of file names, return a list of
        handles to succesfully opened files"""
    files = [os.path.expanduser(item) for item in [file]]
    # If non of these files exist, raise an error
    if not any([os.path.exists(rc) for rc in files]):
        raise RuntimeError("Unable to find config files in these"
                           " locations [%s]" % ", ".join(files))
    return parseConfigs([openFd(item) for item in files])


def parseConfigs(fds):
    """ Given a list of file handles, parse
        all the files with ConfigParser() """
    # Read the config file
    config = SafeConfigParser()
    # Don't transform (lowercase) the key values
    config.optionxform = str
    # Read all the file handles passed
    for fd in fds:
        if fd is None:
            continue
        config.readfp(fd)
    return config
