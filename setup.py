#!/usr/bin/env python

import os
from setuptools import setup
import re
VERSION_FILE = "batch_rpc_monitor/_version.py"
ver_str_line = open(VERSION_FILE, "rt").read()
VS_RE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VS_RE, ver_str_line, re.M)
if mo:
    ver_str = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSION_FILE,))

github_version = os.environ.get('GITHUB_RELEASE_VER')
if github_version:
    if github_version == "v" + ver_str:
        print("Version in _version.py matches the tag name")
    else:
        raise RuntimeError(f"Version in _version.py does not match the tag name (v{ver_str} != {github_version})")
else:
    print("No GITHUB_RELEASE_VER env variable, skipping version check")

setup(name='batch_rpc_monitor',
      version=ver_str,
      # list folders, not files
      packages=['batch_rpc_monitor'],
      scripts=['batch_rpc_monitor/__main__.py'],
      author='Sieciech Czajka',
      author_email='sieciech.czajka@golem.network',
      url='https://github.com/scx1332/batch-rpc-monitor',
      download_url='https://github.com/scx1332/batch-rpc-monitor/archive/refs/tags/{github_version}.tar.gz',
      keywords=['MultiCall', 'json-rpc', 'web3'],
      install_requires=[
          'aiohttp>=3.8.3',
          'aiohttp_jinja2>=1.5',
          'batch_rpc_provider>=1.2.1',
          'dataclasses_json>=0.5.7',
          'Jinja2>=3.1.2',
          'toml>=0.10.2'
      ],
      classifiers=[
          'Development Status :: 3 - Alpha',
          # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
          'Intended Audience :: Developers',  # Define that your audience are developers
          'Topic :: Software Development :: Build Tools',
          'License :: OSI Approved :: MIT License',  # Again, pick a license
          'Programming Language :: Python :: 3.10',
      ],
      )
