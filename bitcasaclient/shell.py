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

from bitcasa import BitcasaClient, BitcasaFile, BitcasaFolder
from timeit import default_timer as Timer
from argparse import ArgumentParser
from bitcasaclient import config, utils
from datetime import datetime
import requests
import urlparse
import pprint
import sys
import re


def authenticate(client, conf):
    """ Preform some OAuth magic to get our access-token """

    def extract_csrf(text):
        pattern = re.compile(
            r'<input type="hidden" name="csrf_token" value="(.+?)"/>')
        matches = pattern.findall(text)
        return matches[0]

    # First get the login page
    resp = requests.get(client.login_url)
    if resp.status_code != 200:
        raise RuntimeError("GET on '%s' returned '%s'" %
                           (client.login_url, resp.status_code))

    # Apparently there is a token hidden in the page!
    csrf_token = extract_csrf(resp.content)
    print("-- Got Token: %s" % csrf_token)

    # Now POST to the login url
    # This POST is NOT mentioned in the docs under the 'Authentication'
    # tab See ( https://developer.bitcasa.com/docs )
    resp = requests.post(client.login_url, params={
        'user': conf['username'],
        'password': conf['password'],
        'redirect': conf['redirect-url'],
        'csrf_token': csrf_token
    })

    # Now get the Auth Code from the redirect URL
    parsed_url = urlparse.urlparse(resp.url)
    parsed_qs = urlparse.parse_qs(parsed_url.query)
    code = parsed_qs['authorization_code']
    print("-- Got Auth Code: %s" % code)

    # This call makes another call to the API to
    # retrieve the access-token
    client.authenticate(code)

    # Record the access-token so we don't need to get it again
    config.writeTokenFile('~/.bitcasa-token', client)
    return client


def clientFactory(conf):
    """ Create a BitcasaClient with an access-token attached """
    conf = dict(conf.items('bitcasa'))
    token = config.readTokenFile('~/.bitcasa-token')
    client = BitcasaClient(conf['client-id'], conf['secret'],
                           conf['redirect-url'], access_token=token)
    if token:
        print("-- Found ~/.bitcasa-token, using...")
        return client

    # If we don't already have an access-token, authenticate to get one
    return authenticate(client, conf)


def downloadDir(client, conf, path):
    try:
        # Get any completed files from this directory download
        completed = dict(conf.items(path))
    except config.NoSectionError:
        completed = {}

    # Get a listing of the directory files
    folder = client.get_folder(path)
    for item in folder.items:
        if item.path in completed.keys():
            print("-- Skip '%s' - Completed" % item.name)
            continue
        # Skip download of directories
        if isinstance(item, BitcasaFolder):
            print("-- Skip '%s' - Folder" % (item.name))
            continue
        # Only Download Files
        if isinstance(item, BitcasaFile):
            download_bitcasa_file(client, conf, item)
            # Add the file to the completed list
            completed[item.path] = item.name
            config.saveCompleted(conf, path, completed, '~/.bitcasa')
            continue
        print("-- Skip '%s' - Unknown Item" % item)

    # If this was a resumed download, remove the section
    if conf.remove_section(path):
        # If the remove found specified section, write the config
        config.saveConfig(conf, '~/.bitcasa')
    return 0


def downloadFile(client, conf, path):
    # First fetch info on the file (file size, etc)
    bitcasa_file = client.get_file(path)
    # Then download the file
    download_bitcasa_file(client, conf, bitcasa_file)


def handle_downloadFile(client, conf, file, force=False):
    def updateProgress(elapsed):
        if conf.opt.no_progress:
            return
        percent = round((float(total_bytes) / file.size) * 100, 2)
        kbs = (float(bytes) / elapsed) / 1024
        sys.stdout.write('\r[{0}] {1}%  {2:.2f} KB/s      '
                         .format(('='*int((percent/10))).ljust(10),
                                 percent, kbs))

    start, count, bytes, total_bytes = Timer(), 0, 0, 0
    with open(file.name, 'w') as fd:
        # Fetch the file as a chunked http response
        for chunk in client.get_file_contents(file.name, file.path):
            # Write the chunk
            fd.write(chunk)
            # Record the number of bytes received for speed calculation
            bytes += len(chunk)
            # Record the total number of bytes for precent calculation
            total_bytes += len(chunk)
            # Count the number of chunks
            count += 1
            # Update progress every 20 chunks
            if (count % 30) == 0 and count != 0:
                updateProgress((Timer() - start))
                # Reset the start time and the transfered bytes
                start = Timer()
                bytes = 0
    updateProgress((Timer() - start))
    sys.stdout.write('\n')
    return total_bytes


def download_bitcasa_file(client, conf, file):
    print("-- Downloading '%s' (%s)" % (file.name, file.path))
    totalAttempts = 2

    # If file exists, and is of correct size don't
    # download again unless overwrite is requested
    size = utils.isComplete(file)
    if size != 0 and not conf.opt.overwrite:
        print("-- File '%s' exists, Skip.." % file.name)
        return

    attempt, size = totalAttempts, 0
    while attempt != 0:
        start = Timer()
        # Preform the download and display progress bar
        size = handle_downloadFile(client, conf, file)
        elapsed = (Timer() - start)
        print("-- %s (%.2f KB/s) - %s saved [%s/%s]" % (
            datetime.today(),
            (float(file.size) / elapsed) / 1024,
            file.name, size, file.size))

        # If the file sizes match, download is complete
        if size == file.size:
            return size

        attempt -= 1
        def retryMessage():
            if attempt == 0:
                return "Failed, Retries exhausted"
            return "Retry attempt '%d'" % (abs(totalAttempts - attempt) + 1)
        print("-- File download was incomplete - %s" % retryMessage())
    return size


def fromList(client, conf, fileName):
    """ fileName must consist of bitcasa paths separated by a newline """

    with open(fileName) as fd:
        for line in fd:
            # Skip comment lines
            if re.match("^#", line):
                continue
            downloadFile(client, conf, line.rstrip())


def main():
    try:
        p = ArgumentParser("bitcasa downloader")
        p.add_argument('command', choices=['ls', 'get', 'get-dir', 'from-list'],
                       help="CLI Command to execute (See Commands)")
        p.add_argument('path', help="Path the command will operate on")
        p.add_argument('-p', '--no-progress', action='store_const', const=True,
                       default=False, help="Silence the progress bar")
        p.add_argument('-o', '--overwrite', action='store_const', const=True,
                       default=False, help="Forces download even if the file "
                       "exists locally and is of correct size")
        opt = p.parse_args()

        # Read the config file and create a client
        conf = config.readConfig('~/.bitcasa')
        # Add the options to the config object
        conf.opt = opt
        # Create the Bitcasa Client
        client = clientFactory(conf)

        # Directory listing
        if opt.command == 'ls':
            folder = client.get_folder(opt.path)
            print(folder)
            for item in folder.items:
                #print("Name: %s - %s" % (item.name, item.path))
                print(item)
            return 0

        # Download a single file
        if opt.command == 'get':
            return downloadFile(client, conf, opt.path)

        # Download an entire directory
        if opt.command == 'get-dir':
            return downloadDir(client, conf, opt.path)

        # Download a list of paths specified in file
        if opt.command == 'from-list':
            return fromList(client, conf, opt.path)

    except RuntimeError, e:
        print(str(e), file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
