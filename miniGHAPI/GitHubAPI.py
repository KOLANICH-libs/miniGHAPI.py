import typing

from .APICore import GHApiObj, GHAPIBase
from .Actions import Actions


class GHAPI(GHAPIBase):
	__slots__ = ()

	def repo(self, owner: str, repo: str):
		return Repo(self, owner, repo)

	def org(self, owner: str):
		return Org(self, owner)


class Repository(GHApiObj):
	__slots__ = ("owner", "repo", "actions")

	def __init__(self, parent, owner: str, repo: str, dbID: int = None ):
		super().__init__(parent, dbID)
		self.owner = owner
		self.repo = repo
		self.actions = Actions(self)

	def _getDBID(self):
		return int(self.gqlReq("query($owner: String!, $repo: String!) {repository(name: $repo, owner: $owner) {databaseId}}", {"owner": parent.owner, "repo": parent.repo, "no": self.no})["data"][ "repository"]["databaseId"])

	@property
	def prefix(self) -> str:
		return "repos/" + self.owner + "/" + self.repo + "/"

	def issue(self, no: int):
		return Issue(self, no)

	def expell(self, user: str):
		self.req("collaborators/" + user, None, method="DELETE", previews=("inertia",))

	def getIssues(self, labels: typing.Optional[str] = None, state: typing.Optional[str] = None):
		q = {}
		if labels is not None:
			if not isinstance(labels, str):
				labels = ",".join(labels)
			q["labels"] = labels
		if state is not None:
			q["state"] = state
		return self.req("issues", q, method="GET").json()

	def sendChecksRun(self, obj):
		return self.req("check-runs", obj).json()

	def patchChecksRun(self, iD, obj):
		return self.req("check-runs/" + str(iD), obj, method="PATCH").json()

	def dispatch(self, payload=None):
		if payload is None:
			payload = {}

		return self.req("dispatches", {"client_payload": payload})

Repo = Repository


class Issue(GHApiObj):
	__slots__ = ("no", )

	def __init__(self, parent, no: int, dbID: str = None):
		super().__init__(parent, dbID)
		self.no = no

	@property
	def prefix(self) -> str:
		return "issues/" + str(self.no) + "/"

	def _getDBID(self):
		return int(self.gqlReq("query($owner: String!, $repo: String!, $no: Int!) {repository(name: $repo, owner: $owner) {issue(number: $no) {databaseId}}}", {"owner": parent.owner, "repo": parent.repo, "no": self.no})["data"][ "repository"]["issue"]["databaseId"])

	def leaveAComment(self, body: str):
		self.req("comments", {"body": str(body)})

	def setLabels(self, labels: typing.Iterable[str]):
		self.req("labels", {"labels": list(labels)}, method="PUT")

	def patch(self, patch: typing.Mapping[str, typing.Any]):
		self.req(patch, method="patch")

	def close(self):
		self.patch({"state": "closed"})

	def open(self):
		self.patch({"state": "open"})

	def delete(self):
		self.req(method="DELETE")
		#mutation ($id: ID!) {deleteIssue(input: {issueId: $id}) {clientMutationId}}

	def lock(self, reason: str = None):
		self.req("lock", {"lock_reason": reason} if reason else None, method="put")

	def unlock(self):
		self.req("lock", None, method="DELETE")

	def move(self, repo):
		return self.gqlReq("mutation ($ii: ID!, $ri: ID!) {transferIssue(input: {issueId: $ii, repositoryId: $ri}) {issue{id}}}", {"ii": self.nodeID, "ri": repo.nodeID})

	def react(self, reaction: str):
		self.req("reactions", {"content": reaction}, method="PUT", previews=("sailor-v", "squirrel-girl"))

	def getEvents(self):
		return self.req("events", previews=("sailor-v", "starfox")).json()


class Organization(GHApiObj):
	__slots__ = ("name", "actions")

	def __init__(self, parent, name: str):
		super().__init__(parent)
		self.name = name
		self.actions = Actions(self)

	@property
	def prefix(self) -> str:
		return "orgs/" + str(self.name) + "/"

	def block(self, user: str):
		self.req("blocks/" + user, None, method="PUT", previews=("giant-sentry-fist",))

	def unblock(self, user: str):
		self.req("blocks/" + user, None, method="DELETE", previews=("giant-sentry-fist",))

Org = Organization
