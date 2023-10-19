miniGHAPI.py [![Unlicensed work](https://raw.githubusercontent.com/unlicense/unlicense.org/master/static/favicon.png)](https://unlicense.org/)
============
[![Libraries.io Status](https://img.shields.io/librariesio/github/KOLANICH-libs/miniGHAPI.py.svg)](https://libraries.io/github/KOLANICH-libs/miniGHAPI.py)
[![Code style: antiflash](https://img.shields.io/badge/code%20style-antiflash-FFF.svg)](https://codeberg.org/KOLANICH-tools/antiflash.py)

**We have moved to https://codeberg.org/KOLANICH-libs/miniGHAPI.py, grab new versions there.**

Under the disguise of "better security" Micro$oft-owned GitHub has [discriminated users of 1FA passwords](https://github.blog/2023-03-09-raising-the-bar-for-software-security-github-2fa-begins-march-13/) while having commercial interest in success and wide adoption of [FIDO 1FA specifications](https://fidoalliance.org/specifications/download/) and [Windows Hello implementation](https://support.microsoft.com/en-us/windows/passkeys-in-windows-301c8944-5ea2-452b-9886-97e4d2ef4422) which [it promotes as a replacement for passwords](https://github.blog/2023-07-12-introducing-passwordless-authentication-on-github-com/). It will result in dire consequencies and is competely inacceptable, [read why](https://codeberg.org/KOLANICH/Fuck-GuanTEEnomo).

If you don't want to participate in harming yourself, it is recommended to follow the lead and migrate somewhere away of GitHub and Micro$oft. Here is [the list of alternatives and rationales to do it](https://github.com/orgs/community/discussions/49869). If they delete the discussion, there are certain well-known places where you can get a copy of it. [Read why you should also leave GitHub](https://codeberg.org/KOLANICH/Fuck-GuanTEEnomo).

---

A small library for interacting with GitHub intended to be used in GitHub Actions implemented in python.

Most of the actions must be authenticated. You need different tokens depending on your use case:

* `env["INPUT"]["GITHUB_TOKEN"]` to work with issues or send annotations
* `env["ACTIONS"]["RUNTIME_TOKEN"]` to work with undocumented API, such as creating artifacts, working with cache or sending SARIF analytics

Actions retrieving collections populate properties. Use `get*` methods to fetch them and populate.

The lib also contains some bindings to undocumented API, allowing you to upload files for workflows.


Dependencies
------------

* [`requests`](https://github.com/psf/requests)[![PyPi Status](https://img.shields.io/pypi/v/requests.svg)](https://pypi.org/pypi/requests)[![GitHub Actions](https://github.com/psf/requests/workflows/run-tests/badge.svg)](https://github.com/psf/requests/actions/)[![Libraries.io Status](https://img.shields.io/librariesio/github/psf/requests.svg)](https://libraries.io/github/psf/requests)![License](https://img.shields.io/github/license/psf/requests.svg) or [`httpx`](https://github.com/encode/httpx)[![PyPi Status](https://img.shields.io/pypi/v/httpx.svg)](https://pypi.org/pypi/httpx)[![GitHub Actions](https://github.com/encode/httpx/workflows/Test%20Suite/badge.svg)](https://github.com/encode/httpx/actions/)[![Libraries.io Status](https://img.shields.io/librariesio/github/encode/httpx.svg)](https://libraries.io/github/encode/httpx)
