__all__ = ("GHApiObj", "json")

import typing
from enum import Enum
from os import environ
from urllib.parse import urlencode

from .idConvert import dbIDAndType2NodeID, nodeID2DBIDAndType
from .utils import httpx, iterateSlice, json

#gh api is not working this way
#import certifi
#from urllib3 import PoolManager
#import urllib3.contrib.pyopenssl
#urllib3.contrib.pyopenssl.inject_into_urllib3()
#certsStore = certifi.where()
#http = PoolManager(ca_certs=certsStore, cert_reqs="CERT_REQUIRED")

MAIN_DOMAIN = "github.com"
GH_API_BASE = "https://api.github.com/"
USERCONTENT_DOMAIN = "raw.githubusercontent.com"


class GHApiObj_:
	__slots__ = ()

	@property
	def prefix(self) -> str:
		raise NotImplementedError()

	def req(self, path: str = "/", obj: typing.Union[typing.Mapping[str, typing.Any], bytes] = None, method: typing.Optional[str] = "post", previews: typing.Tuple[str] = (), urlParams=None):
		raise NotImplementedError()

	@property
	def root(self):
		raise NotImplementedError()

	@property
	def env(self) -> dict:
		return self.root.env


def iteratePaginationSlice(slc: slice):
	return iterateSlice(slc, defaultStart=1)


GH_CT_PREFIX = "application/vnd.github"


class ContentType(Enum):
	"""https://docs.github.com/en/rest/overview/media-types"""

	json = GH_CT_PREFIX + "+json"
	raw = GH_CT_PREFIX + ".raw+json"
	raw_base64 = GH_CT_PREFIX + ".raw"
	base64 = GH_CT_PREFIX + ".base64"
	text = GH_CT_PREFIX + ".text+json"
	html = GH_CT_PREFIX + ".html+json"
	full = GH_CT_PREFIX + ".full+json"
	diff = GH_CT_PREFIX + ".diff"
	patch = GH_CT_PREFIX + ".patch"
	sha = GH_CT_PREFIX + ".sha"

CT = ContentType

class GHAPIBase(GHApiObj_):
	__slots__ = ("hdrz", "GH_API_BASE", "env", "timeout")

	def _getAPIRoot(self):
		if self.env is not None:
			return self.env["GITHUB"]["API_URL"] + "/"
		else:
			return GH_API_BASE

	def getDefaultAccept(self) -> str:
		return CT.raw.value

	def getContentType(self) -> str:
		return "application/json"

	def getDefaultAuthToken(self) -> str:
		return self.env["ACTIONS"]["RUNTIME_TOKEN"]

	def getAuth(self, token: str) -> str:
		if token:
			return "Bearer " + token

	def __init__(self, token: str, userAgent: str = None, env: dict = None, timeout: float = 5):
		self.timeout = timeout
		self.env = env
		if token is None:
			token = self.getDefaultAuthToken()
		auth = self.getAuth(token)
		hdrz = {"Content-Type": self.getContentType(), "Accept": self.getDefaultAccept()}
		if auth:
			hdrz["Authorization"] = auth

		if userAgent:
			hdrz["User-Agent"] = userAgent
		self.hdrz = hdrz

		self.GH_API_BASE = self._getAPIRoot()

	@property
	def root(self):
		return self

	@property
	def prefix(self) -> str:
		return self.GH_API_BASE

	def _genHeadersWithPreviews(self, previews: typing.Tuple[str] = ()) -> dict:
		hdrz = type(self.hdrz)(self.hdrz)
		if previews:
			hdrz["Accept"] = ", " + (", ".join((GH_CT_PREFIX + "." + preview + "-preview") for preview in previews))
		return hdrz

	def scrapeEndpointBase(fetchFunc, endpointBase, extractorFunc, accum, logArea, whitelisted):
		def parsePage(e):
			e = json.loads(e)
			if len(e):
				if 1 == e.length and not e[0]:
					return accum

				for m in e:
					el = extractorFunc(m)
					if whitelisted.has(el):
						accum.add(el)

				return fetchAndParsePage(page + 1)

			return accum

		def fetchAndParsePage(e):
			return fetchFunc(endpointBase + e, additional).then(parsePage)

		endpointBase += "?"
		return fetchAndParsePage(1)

	@classmethod
	def _makeReqPaginated(cls, method, uri, data: typing.Optional[bytes], hdrz, urlParams, pagination: slice):
		if urlParams is None:
			urlParams = {}

		urlParams["per_page"] = 100
		for pageNo in iteratePaginationSlice(pagination):
			urlParams["page"] = pageNo
			print("Request:", method, uri, data, hdrz, urlParams)
			res = httpx.request(method, uri, data=data, headers=hdrz, params=urlParams, timeout=None)
			res.raise_for_status()
			yield res

			if "next" not in res.links:
				break

	@classmethod
	def _makeReqMaybePaginated(cls, method, uri, data: typing.Optional[bytes], hdrz, urlParams, pagination: typing.Optional[slice] = None):
		if not isinstance(pagination, (range, slice)):
			print("Request:", method, uri, data, hdrz, urlParams)
			res = httpx.request(method, uri, data=data, headers=hdrz, params=urlParams, timeout=None)
			res.raise_for_status()
			return res
		else:
			return cls._makeReqPaginated(method, uri, data, hdrz, urlParams, pagination)

	def req(self, path: str = "/", obj: typing.Union[typing.Mapping[str, typing.Any], bytes] = None, method: typing.Optional[str] = None, previews: typing.Tuple[str] = (), urlParams=None, contentType: typing.Union[str, CT] = None, contentRange: range = None, accept: typing.Union[str, CT] = None, pagination: typing.Optional[slice] = None) -> httpx.Response:
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

		if isinstance(contentType, Enum):
			contentType = contentType.value

		if contentType is not None:
			hdrz["Content-Type"] = contentType

		if isinstance(accept, Enum):
			accept = accept.value

		if accept is not None:
			hdrz["Accept"] = accept

		if obj is not None:
			if isinstance(obj, str):
				data = obj.encode("utf-8")
			elif isinstance(obj, bytes):
				data = obj
				if contentRange is not None:
					if isinstance(contentRange, range):
						bytesRange = contentRange
						totalSize = None
					else:
						totalSize = contentRange[1]
						bytesRange = contentRange[0]

					hdrz["Content-Range"] = "bytes " + str(bytesRange.start) + "-" + str(bytesRange.stop - 1) + "/" + ("*" if totalSize is None else str(totalSize))
			else:
				if method == "GET":
					if urlParams is None:
						urlParams = {}
					urlParams.update(obj)
					data = None
				else:
					data = json.dumps(obj)

		res = self._makeReqMaybePaginated(method, self.prefix + path, data=data if obj is not None else None, hdrz=hdrz, urlParams=urlParams, pagination=pagination)
		return res

	def gqlReq(self, query: str, previews: typing.Tuple[str] = (), **args: dict) -> typing.Union[list, dict]:
		data = json.dumps({"query": query, "variables": args})
		res = httpx.request("POST", self.GH_API_BASE + "graphql", data=data, headers=self._genHeadersWithPreviews(previews), timeout=None)
		res.raise_for_status()
		return json.loads(res.data.decode("utf-8"))


class UndocumentedAPIRoot(GHAPIBase):
	"""Undocumented API roots live within own domains and are pretty separated from the rest of API"""

	__slots__ = ("someId",)

	UNDOCUMENTED_API_VERSION = "6.0"
	API_VERSION_ARG_NAME = "api-version"
	API_VERSION_ARG_VALUE = UNDOCUMENTED_API_VERSION + "-preview"
	API_VERSION_ARG_NAME_VALUE_PAIR = API_VERSION_ARG_NAME + "=" + API_VERSION_ARG_VALUE
	API_VERSION_ARG_NAME_VALUE_DIC = {API_VERSION_ARG_NAME: API_VERSION_ARG_VALUE}
	API_VERSION_ARG_NAME_VALUE_DIC = {}

	USER_CONTENT_DOMAIN = "githubusercontent.com"
	ACTIONS_USER_CONTENT_DOMAIN = "actions." + USER_CONTENT_DOMAIN

	# must be set
	SUBDOMAIN = None
	ENV_VAR = None

	def _genHeadersWithPreviews(self, previews: typing.Tuple[str] = ()) -> dict:
		hdrz = type(self.hdrz)(self.hdrz)
		if previews:
			raise ValueError("Previews are not allowed here")
		return hdrz

	def getDefaultAccept(self):
		return "application/json;" + self.__class__.API_VERSION_ARG_NAME_VALUE_PAIR

	@classmethod
	def getACTIONS_RUNTIME_URL(cls, someId: str):
		return "https://" + cls.SUBDOMAIN + "." + cls.ACTIONS_USER_CONTENT_DOMAIN + "/" + someId + "/"

	def _getAPIRoot(self):
		APIS_POSTFIX = "_apis/"
		if self.someId is None:
			return self.env["ACTIONS"][self.__class__.ENV_VAR] + APIS_POSTFIX

		return self.__class__.getACTIONS_RUNTIME_URL(self.someId) + APIS_POSTFIX

	def __init__(self, token: str, userAgent: str = None, env: dict = None, someId: str = None):
		self.someId = someId
		super().__init__(token, userAgent, env)


class GHApiObj(GHApiObj_):  # pylint:disable=abstract-method
	__slots__ = ("parent", "_dbID", "info")

	INFOABLE = False  # Determines if info dict can be fetched from the object by a generic URI

	def __init__(self, parent: typing.Union["GHApiObj", GHAPIBase], dbID: typing.Optional[int] = None, info: typing.Optional[dict] = None):
		self.parent = parent
		self._dbID = dbID
		self.info = info

	def getInfo(self, fresh: bool = False, accept: str = CT.json):
		if self.__class__.INFOABLE:
			if self.info is None or fresh:
				res = self.req("", None, method="GET", accept=accept).json()
				self._dbID = res["id"]
				self.info = res
				return res
			else:
				return self.info
		else:
			raise NotImplementedError

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
		self._dbID = iD

	def _getDBID(self):
		self.getInfo()  # updates self._dbID as a side effect
		return self._dbID

	@property
	def root(self):
		el = self
		while not isinstance(el, GHAPIBase):
			el = el.parent

		return el

	@property
	def env(self) -> dict:
		return self.root.env

	def req(self, path: str = "/", obj=None, method: str = "POST", previews: typing.Tuple[str] = (), urlParams=None, contentType: str = None, contentRange: range = None, accept: str = None, pagination: typing.Optional[slice] = None) -> httpx.Response:
		return self.parent.req(self.prefix + path, obj, method=method, previews=previews, urlParams=urlParams, contentType=contentType, contentRange=contentRange, accept=accept, pagination=pagination)

	def gqlReq(self, query: str, previews: typing.Tuple[str] = (), **args: dict) -> typing.Union[list, dict]:
		return self.parent.gqlReq(query, previews=previews, **args)
