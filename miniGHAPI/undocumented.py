import os
from pathlib import PurePath

from .Actions import *
from .APICore import GHAPIBase, GHApiObj, UndocumentedAPIRoot


class RunIddableUndocumented(GHApiObj):
	__slots__ = ("runId",)
	PREFIX = None

	def __init__(self, parent, iD: int, dbID=None):
		super().__init__(parent, dbID=dbID)
		if iD is None:
			iD = int(self.env["GITHUB"]["RUN_ID"])

		self.runId = iD

	@property
	def prefix(self) -> str:
		return self.__class__.PREFIX + str(self.runId) + "/"


def getArtifactsCacheEndpoint(shittyId, key: str, version: str):
	"""version looks like SHA256 hash"""
	return ARTIFACTS_CACHE_API + shittyId + ARTIFACTS_CACHE_API + "?keys=" + key + "&version=" + version


class PipelinesAPIRoot(UndocumentedAPIRoot):
	__slots__ = ("resources", "pipelines")

	SUBDOMAIN = "pipelines"
	ENV_VAR = "RUNTIME_URL"

	def __init__(self, token: str, userAgent: str = None, env: dict = None, someId: str = None):
		super().__init__(token, userAgent, env, someId)
		self.pipelines = PipelinesUndocumented(self)
		self.resources = ResourcesUndocumented(self)


class ArtifactsUploader:
	__slots__ = ("parent", "container", "name")

	def __init__(self, parent, name: str):
		self.parent = parent
		self.name = name
		self.container = None

	def __enter__(self):
		if self.container is None:
			self.container = self.parent.workflows.artifacts.createContainer(self.name)
			self.name = None

		return self

	def __setitem__(self, k, v):
		res = self.container.putArtifact(k, v)
		print("put res:", res)

	def __exit__(self, *args, **kwargs):
		# The following line is required in order for an artifact to appear within a pipeline!!!
		res1 = self.parent.workflows.artifacts.patchArtifact({}, self.container.name)  # patched with "Size": len(fileContents) by default, but it takes no effect: it works both even if I removed it, and if I filled it with misinformation. ToDo: find out what else I can use here!
		print("patch res:", res1)


class PipelinesUndocumented(GHApiObj):
	__slots__ = ("workflows",)

	def getArtifactUploader(self, name) -> ArtifactsUploader:
		return ArtifactsUploader(self, name)

	@property
	def prefix(self) -> str:
		return "pipelines/"

	def __init__(self, parent, dbID: int = None):
		super().__init__(parent=parent, dbID=dbID)
		self.workflows = WorkflowsUndocumented(self)


class ResourcesUndocumented(GHApiObj):
	__slots__ = ("containers",)

	@property
	def prefix(self):
		return "resources/"

	def __init__(self, parent, runId: int = None):
		super().__init__(parent, runId)
		self.containers = ContainersUndocumented(self)


class ContainersUndocumented(GHApiObj):
	__slots__ = ()

	@property
	def prefix(self) -> str:
		return "Containers/"

	def __getitem__(self, iD: int):
		return Container(self, iD, None)


class File:
	__slots__ = ("parent", "name", "size")

	def __init__(self, parent, name: PurePath, size: int):
		assert name is not None
		self.name = name
		self.parent = parent
		self.size = size

	def __getitem__(self, k):
		raise NotImplementedError

	def __setitem__(self, k: slice, v: bytes):
		if k is not None:
			if not isinstance(k, slice):
				raise ValueError("Key must be a slice")
		else:
			k = range(len(v))

		if self.size is None:
			self.size = len(v)

		return self.parent.req("", obj=v, method="PUT", urlParams={"itemPath": str(PurePath(self.parent.name) / self.name)}, contentType="application/octet-stream", contentRange=(k, self.size)).json()
		# {"containerId": 266701, "scopeIdentifier": "00000000-0000-0000-0000-000000000000", "path": "test.txt/test.txt", "itemType": "file", "status": "created", "fileLength": 5, "fileEncoding": 1, "fileType": 1, "dateCreated": <ISO date time string>, "dateLastModified": <ISO date time string>, "createdBy":  <guid>, "lastModifiedBy": <guid>, "fileId": 1207, "contentId": ""}


class Container(GHApiObj):
	__slots__ = ("id", "name", "expiration")

	def __init__(self, parent, iD: int, name: str = None, expiration: int = None, dbID=None):
		super().__init__(parent, dbID=dbID)
		self.id = iD
		self.name = name
		self.expiration = expiration

	@property
	def prefix(self) -> str:
		return str(self.id)

	def file(self, name: PurePath, size: int = None):
		return File(self, name, size)

	def putArtifact(self, fileName: PurePath, fileContents: bytes) -> dict:
		f = self.file(fileName)
		f[None] = fileContents


class WorkflowsUndocumented(RunIddableUndocumented):
	__slots__ = ("artifacts",)
	PREFIX = "workflows/"

	def __init__(self, parent, runId: int = None):
		super().__init__(parent, runId)
		self.artifacts = ArtifactsUndocumented(self)


class ArtifactsUndocumented(GHApiObj):
	__slots__ = ()

	@property
	def prefix(self) -> str:
		return "artifacts"

	def createContainer(self, containerName: str, days: int = None) -> "Container":
		reqObj = {"Type": "actions_storage", "Name": containerName}
		if days is not None:
			maxRetentionDays = int(self.env["GITHUB"]["RETENTION_DAYS"])
			if days > maxRetentionDays:
				raise ValueError("Retention for " + str(days) + " is not allowed for this repo")
			reqObj["RetentionDays"] = days

		res = self.req(path="", obj=reqObj, method="post").json()
		c = self.root.resources.containers[res["containerId"]]
		c.name = containerName
		c.expiration = res["expiresOn"]
		return c

	def patchArtifact(self, dic: dict, containerName: str) -> dict:
		return self.req("", obj=dic, method="PATCH", urlParams={"artifactName": containerName}).json()


# https://github.com/actions/toolkit/blob/main/packages/cache/src/cache.ts
class ArtifactCacheAPIRoot(UndocumentedAPIRoot):
	__slots__ = ("cache",)

	SUBDOMAIN = "artifactcache"
	ENV_VAR = "RUNTIME_URL"

	class CacheUndocumented(RunIddableUndocumented):
		__slots__ = ()
		PREFIX = "artifactcache/cache/"

	def __init__(self, token: str, userAgent: str = None, env: dict = None, someId: str = None):
		super().__init__(token, userAgent, env, someId)
		self.cache = CacheUndocumented(self)
