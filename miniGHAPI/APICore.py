__all__ = ("GHApiObj", "json")

import typing
from urllib.parse import urlencode

#gh api is not working this way
#import certifi
#from urllib3 import PoolManager
#import urllib3.contrib.pyopenssl
#urllib3.contrib.pyopenssl.inject_into_urllib3()
#certsStore = certifi.where()
#http = PoolManager(ca_certs=certsStore, cert_reqs="CERT_REQUIRED")

try:
	import requests
except ImportError:
	import httpx as requests

from .idConvert import nodeID2DBIDAndType, dbIDAndType2NodeID
from .utils import json

GH_API_BASE = "https://api.github.com/"


class GHApiObj_:
	__slots__ = ()

	@property
	def prefix(self) -> str:
		raise NotImplementedError()

	def req(self, path, obj, method="post"):
		raise NotImplementedError()


class GHAPIBase(GHApiObj_):
	__slots__ = ("hdrz", "GH_API_BASE")

	def __init__(self, token, userAgent=None, env=None):
		hdrz = {"Authorization": "Bearer " + token, "Content-Type": "application/json", "Accept": "application/vnd.github.raw+json"}
		if userAgent:
			hdrz["User-Agent"] = userAgent
		self.hdrz = hdrz

		if env is not None:
			self.GH_API_BASE = env["GITHUB"]["API_URL"] + "/"
		else:
			self.GH_API_BASE = GH_API_BASE

	@property
	def prefix(self) -> str:
		return self.GH_API_BASE

	def _genHeadersWithPreviews(self, previews: typing.Tuple[str] = ()) -> dict:
		hdrz = type(self.hdrz)(self.hdrz)
		if previews:
			hdrz["Accept"] = ", " + (", ".join(("application/vnd.github." + preview + "-preview") for preview in previews))
		return hdrz

	def req(self, path: str = "/", obj=None, method: typing.Optional[str] = None, previews: typing.Tuple[str] = ()) -> requests.Response:
		if path[-1:] == "/":
			path = path[:-1]

		if method is None:
			if obj is None:
				method = "GET"
			else:
				method = "POST"
		else:
			method = method.upper()

		hdrz = self._genHeadersWithPreviews(previews)

		if method == "GET":
			path += "?" + urlencode(obj)
			data = None
		else:
			data = json.dumps(obj)

		#res = http.request(method, self.prefix + path, body=data.encode("utf-8") if obj is not None else b"", headers=hdrz)
		res = requests.request(method, self.prefix + path, data=data if obj is not None else None, headers=hdrz)
		#return res.data.decode("utf-8")
		res.raise_for_status()
		return res

	def gqlReq(self, query: str, previews: typing.Tuple[str] = (), **args: dict) -> typing.Union[list, dict]:
		data = json.dumps({"query": query, "variables": args})
		res = requests.request("POST", self.GH_API_BASE + "graphql", data=data, headers=self._genHeadersWithPreviews(previews))
		res.raise_for_status()
		return json.loads(res.data.decode("utf-8"))


class GHApiObj(GHApiObj_):  # pylint:disable=abstract-method
	__slots__ = ("parent", "_dbID")

	def __init__(self, parent, dbID: int=None):
		self.parent = parent
		self._dbID = dbID

	@property
	def dbID(self):
		if not self._dbID:
			self._dbID = self._getDBID()
		return self._dbID

	@dbID.setter
	def dbID(self, v: int):
		self._dbID = v

	@property
	def nodeID(self):
		return dbIDAndType2NodeID(self.dbID, self.__class__.__name__)

	@nodeID.setter
	def nodeID(self, v: int):
		iD, cName = nodeID2DBIDAndType(self.dbID)
		if self.__class__.__name__ != cName:
			raise ValueError("Node ID from another type", cName)
		self.dbID = iD

	def _getDBID(self):
		raise NotImplementedError

	def req(self, path: str = "/", obj=None, method: str = "POST", previews: typing.Tuple[str] = ()) -> requests.Response:
		return self.parent.req(self.prefix + path, obj, method=method, previews=previews)

	def gqlReq(self, query: str, previews: typing.Tuple[str] = (), **args: dict) -> typing.Union[list, dict]:
		return self.parent.gqlReq(query, previews=previews, **args)
