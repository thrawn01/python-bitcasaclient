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

import os


def fileSize(fileName):
    """ This should be a platform independent
    way to returning the size of a file """
    fd = os.open(fileName, os.O_RDONLY)
    try:
        return os.lseek(fd, 0, os.SEEK_END)
    finally:
        os.close(fd)


def isComplete(file):
    """ If the file exists, and is the same size as the download candidate,
        return the size of the file else return 0 """
    if os.path.exists(file.name):
        size = fileSize(file.name)
        if size == file.size:
            return size
    return 0

