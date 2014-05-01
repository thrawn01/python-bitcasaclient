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

from setuptools import setup, find_packages

setup(
    name='bitcasaclient',
    version='0.1',
    description='A Commandline tool for Bitcasa API',
    author='Derrick J. Wipler',
    packages=find_packages(exclude=['test', 'bin']),
    entry_points={
        'console_scripts': [
            'bitcasa = bitcasaclient.shell:main',
            ],
        }, requires=['requests', 'bitcasa'],
    )
