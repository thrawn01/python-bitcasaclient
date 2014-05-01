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
from argparse import ArgumentParser
from bitcasaclient import config
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


def client_factory(conf):
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


def download_dir(client, conf, download_dir):
    try:
        # Get any completed files from this directory download
        completed = dict(conf.items(download_dir))
    except config.NoSectionError:
        completed = {}

    # Get a listing of the directory files
    folder = client.get_folder(download_dir)
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
            try:
                download_file(item)
                # Add the file to the completed list
                completed[item.path] = item.name
                continue
            except Exception, e:
                # Save our download directory progress
                config.saveCompleted(conf, download_dir, completed)
                # Re-raise the original exception
                raise
        print("-- Skip '%s' - Unknown Item" % item)

    # If this was a resumed download, remove the section
    if conf.remove_section(download_dir):
        # If the remove found the section, write the config
        config.saveConfig(conf)

    pprint.pprint(completed)
    return 0


def download_file(file):
    print("-- Downloading '%s' (%s)" % (file.name, file.path))


def main():
    try:
        p = ArgumentParser("bitcasa downloader")
        p.add_argument('-l', '--list', help="List the contents of a directory")
        p.add_argument('-dd', '--download-dir',
                       help="Download all files in directory (not subfolders)")
        args = p.parse_args()

        # Read the config file and create a client
        conf = config.readConfig('~/.bitcasa')
        client = client_factory(conf)

        # If we only want a directory listing
        if args.list:
            folder = client.get_folder(args.list)
            print(folder)
            for item in folder.items:
                #print("Name: %s - %s" % (item.name, item.path))
                print(item)
            return 0

        # If we want to download a entire directory
        if args.download_dir:
            return download_dir(client, conf, args.download_dir)

    except RuntimeError, e:
        print(str(e), file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
