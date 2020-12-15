miniGHAPI.py [![Unlicensed work](https://raw.githubusercontent.com/unlicense/unlicense.org/master/static/favicon.png)](https://unlicense.org/)
============
[![Libraries.io Status](https://img.shields.io/librariesio/github/KOLANICH-libs/miniGHAPI.py.svg)](https://libraries.io/github/KOLANICH-libs/miniGHAPI.py)
[![Code style: antiflash](https://img.shields.io/badge/code%20style-antiflash-FFF.svg)](https://codeberg.org/KOLANICH-tools/antiflash.py)

A small library for interacting with GitHub intended to be used in GitHub Actions implemented in python.

Most of the actions must be authenticated. You need different tokens depending on your use case:

* `env["INPUT"]["GITHUB_TOKEN"]` to work with issues or send annotations
* `env["ACTIONS"]["RUNTIME_TOKEN"]` to work with undocumented API, such as creating artifacts, working with cache or sending SARIF analytics

Actions retrieving collections populate properties. Use `get*` methods to fetch them and populate.

The lib also contains some bindings to undocumented API, allowing you to upload files for workflows.


Dependencies
------------

* [`requests`](https://github.com/psf/requests)[![PyPi Status](https://img.shields.io/pypi/v/requests.svg)](https://pypi.org/pypi/requests)[![GitHub Actions](https://github.com/psf/requests/workflows/run-tests/badge.svg)](https://github.com/psf/requests/actions/)[![Libraries.io Status](https://img.shields.io/librariesio/github/psf/requests.svg)](https://libraries.io/github/psf/requests)![License](https://img.shields.io/github/license/psf/requests.svg) or [`httpx`](https://github.com/encode/httpx)[![PyPi Status](https://img.shields.io/pypi/v/httpx.svg)](https://pypi.org/pypi/httpx)[![GitHub Actions](https://github.com/encode/httpx/workflows/Test%20Suite/badge.svg)](https://github.com/encode/httpx/actions/)[![Libraries.io Status](https://img.shields.io/librariesio/github/encode/httpx.svg)](https://libraries.io/github/encode/httpx)
