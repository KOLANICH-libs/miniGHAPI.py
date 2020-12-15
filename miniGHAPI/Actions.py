import typing

from .APICore import GHApiObj


class Artifact(GHApiObj):
	__slots__ = ("id",)

	def __init__(self, parent, iD: int):
		super().__init__(parent)
		self.id = iD

	@property
	def prefix(self) -> str:
		return str(self.id) + "/"

	def info(self) -> str:
		return self.req().json()

	def download(self, archiveFormat: str) -> str:
		return self.req(archiveFormat)

	def delete(self) -> str:
		return self.req(method="DELETE")


class Artifacts(GHApiObj):
	__slots__ = ()

	@property
	def prefix(self) -> str:
		return "artifacts/"

	def __iter__(self):
		return self.req().json()["artifacts"]

	def __getitem__(self, iD: int) -> Artifact:
		return Artifact(self, iD)


class WorkflowRun(GHApiObj):
	__slots__ = ("id",)

	def __init__(self, parent, iD: int):
		super().__init__(parent)
		self.id = iD

	@property
	def prefix(self) -> str:
		return str(self.id) + "/"

	def info(self):
		return self.req().json()

	def rerun(self):
		return self.req("rerun")

	def artifacts(self):
		return self.req("artifacts").json()["artifacts"]

	def cancel(self):
		return self.req("cancel")

	def logs(self, method="GET"):
		return self.req("logs", method=method)

	def timing(self):
		return self.req("timing").json()


Run = WorkflowRun


class Runs(GHApiObj):
	__slots__ = ()

	@property
	def prefix(self) -> str:
		return "runs/"

	def get(self, **kwargs: dict):
		"""https://developer.github.com/v3/actions/workflow-runs/#list-workflow-runs-for-a-repository"""
		return self.req(obj=kwargs, method="GET").json()["workflow_runs"]

	def __getitem__(self, iD: int):
		return Run(self, iD)


class Secrets(GHApiObj):
	__slots__ = ()

	@property
	def prefix(self) -> str:
		return "secrets/"

	def publicKey(self):
		return self.req("public-key").json()

	def __iter__(self):
		return self.req().json()["secrets"]

	def getInfo(self, key: str):
		return self.req(key).json()

	def put(self, key: str, encrypted: str, keyId: str):
		return self.req(key, {"encrypted_value": encrypted, "key_id": keyId}, method="put")

	def delete(self, key: str):
		return self.req(key, method="DELETE")

	def repos(self, key: str):
		return self.req(key + "/repositories").json()["repositories"]

	def setRepos(self, key: str, repos: typing.List[int]):
		return self.req(key + "/repositories", {"selected_repository_ids": repos}, method="put").json()["repositories"]


class Workflow(GHApiObj):
	__slots__ = ("id",)

	def __init__(self, parent, iD: int):
		super().__init__(parent)
		self.id = iD

	@property
	def prefix(self) -> str:
		return str(self.id) + "/"

	def info(self):
		return self.req().json()

	def timing(self):
		return self.req("timing").json()


class Workflows(GHApiObj):
	__slots__ = ()

	@property
	def prefix(self) -> str:
		return "workflows/"

	def __getitem__(self, iD: int):
		return Workflow(self, iD)


class Actions(GHApiObj):
	__slots__ = ("runs", "artifacts", "secrets", "workflows")

	def __init__(self, parent):
		super().__init__(parent)
		self.artifacts = Artifacts(self)
		self.runs = Runs(self)
		self.secrets = Secrets(self)
		self.workflows = Workflows(self)

	@property
	def prefix(self) -> str:
		return "actions/"
