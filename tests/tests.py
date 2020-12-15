#!/usr/bin/env python3
import sys
from pathlib import Path
import unittest
from unittest.mock import patch, Mock
import itertools
import secrets
from functools import partial

try:
	thisDir = Path(__file__).parent
except NameError:
	thisDir = Path(".")
	if not (thisDir / "tests.py").is_file() and (thisDir / "tests" / "tests.py").is_file():
		thisDir = thisDir / "tests"

sys.path.insert(0, str(thisDir.parent))

from collections import OrderedDict

dict = OrderedDict

from miniGHAPI.GHActionsEnv import getGHEnv
from miniGHAPI.undocumented import PipelinesAPIRoot

mockedFilesDir = thisDir / "mockedFiles"

envMock = {
	"GITHUB": {
		"WORKSPACE": Path("/home/runner/work/miniGHAPI.py/miniGHAPI.py"),
		"PATH": mockedFilesDir / "add_path_<guid>",  # empty file
		"ACTION": "__KOLANICH-GHActions_typical-python-workflow",
		"RUN_NUMBER": "30",
		"ACTIONS": "true",
		"SHA": "0" * 40,
		"REF": "refs/heads/master",
		"API_URL": "https://api.github.com",
		"ENV": mockedFilesDir / "set_env_<guid>",  # empty file
		"EVENT_PATH": mockedFilesDir / "event.json",
		"EVENT_NAME": "push",
		"RUN_ID": "123456789",
		"ACTOR": "KOLANICH",
		"RUN_ATTEMPT": "1",
		"GRAPHQL_URL": "https://api.github.com/graphql",
		"SERVER_URL": "https://github.com",
		"JOB": "build",
		"REPOSITORY": "KOLANICH-libs/miniGHAPI.py",
		"RETENTION_DAYS": "90",
		"ACTION_REPOSITORY": "KOLANICH-GHActions/typical-python-workflow",
		"BASE_REF": "",
		"REPOSITORY_OWNER": "KOLANICH-libs",
		"HEAD_REF": "",
		"ACTION_REF": "master",
		"WORKFLOW": thisDir
	},
	"ACTIONS": {
		"CACHE_URL": "https://artifactcache.actions.githubusercontent.com/bcrGkcMlXtYeqhZzIRjdRohPLCXaKDDOPkBVviZjsOceNhpzrv/",
		"RUNTIME_URL": "https://pipelines.actions.githubusercontent.com/bcrGkcMlXtYeqhZzIRjdRohPLCXaKDDOPkBVviZjsOceNhpzrv/",
		"RUNTIME_TOKEN": "1664_char_token_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
	},
	"INPUT": {
		"SHOULD_ISOLATE_TESTING": "false",
		"GITHUB_TOKEN": "40_char_token_aaaaaaaaaaaaaaaaaaaaaaaaaa",
		"USE_PYTEST": "true"
	},
	"HOME": "/home/runner"
}

simulatedEnv = getGHEnv()
if "GITHUB" not in simulatedEnv or "RUN_ID" not in simulatedEnv["GITHUB"]:
	simulatedEnv = envMock

class Tests(unittest.TestCase):
	@patch("miniGHAPI.GHActionsEnv.getGHEnv", return_value=simulatedEnv)
	def testUploadArtifact(self, getGHEnv):
		env = getGHEnv()
		pu = PipelinesAPIRoot(env["ACTIONS"]["RUNTIME_TOKEN"], "miniGHApi", env=env)
		with pu.pipelines.getArtifactUploader("shit") as u:
			u["crap"] = secrets.token_bytes(8)


if __name__ == "__main__":
	unittest.main()
