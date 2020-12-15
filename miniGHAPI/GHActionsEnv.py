import typing
from collections import defaultdict
from os import environ
from pathlib import Path

ctors = {"WORKSPACE": Path, "WORKFLOW": Path, "HOME": Path}


def postprocessEnviron(e: dict) -> dict:
	for k in tuple(e):
		if k in ctors:
			ctor = ctors[k]
		elif k.endswith("_PATH"):
			ctor = Path
		else:
			continue
		e[k] = ctor(e[k])


def filterEnviron() -> dict:
	pfxes = ("GITHUB", "ACTIONS", "INPUT")
	res = defaultdict(dict)
	for pfx in pfxes:
		pfx_ = pfx + "_"
		l = len(pfx_)
		res[pfx] = {k[l:]: v for k, v in environ.items() if k[:l] == pfx_}
	for k in ("HOME",):
		res[k] = environ[k]
	return res


def getGHEnv() -> dict:
	r = filterEnviron()
	for d in r.values():
		postprocessEnviron(d)
	return r


def getRepo(env: dict) -> typing.Tuple[str, str]:
	owner, name = env["GITHUB"]["REPOSITORY"].split("/")
	return owner, name


def getEvent(env: dict) -> dict:
	from .utils import json

	return json.loads(env["GITHUB"]["EVENT_PATH"].read_text())


def getShittyIdFromACTIONS_RUNTIME_URL():
	from urllib.parse import urlparse

	return next(filter(None, urllib.parse.urlparse(RUNTIME_URL).path.split("/")))


def getSomeShittyId(env: dict) -> str:
	a = env["ACTIONS"]
	someUri = a.get("RUNTIME_URL", None)
	if someUri:
		return getShittyIdFromACTIONS_RUNTIME_URL(someUri)

	someUri = a.get("CACHE_URL", None)
	if someUri:
		return getShittyIdFromACTIONS_RUNTIME_URL(someUri)

	return None
