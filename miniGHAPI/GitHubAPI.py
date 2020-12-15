import base64
import typing
from pathlib import PurePosixPath

from .Actions import Actions
from .APICore import MAIN_DOMAIN, USERCONTENT_DOMAIN, CT, GHAPIBase, GHApiObj
from .utils import httpx


class BlocksMixin:
	__slots__ = ()

	def get(self):
		return self.req("blocks", None, method="GET")

	def block(self, user: str):
		return self.req("blocks/" + user, None, method="PUT")

	def unblock(self, user: str):
		return self.req("blocks/" + user, None, method="DELETE")


class GHAPI(GHAPIBase, BlocksMixin):
	__slots__ = ()

	def repo(self, owner: str, repo: str):
		return Repo(self, owner, repo)

	def org(self, owner: str):
		return Org(self, owner)

	def user(self, owner: str):
		return User(self, owner)


class RepoOwner(GHApiObj):
	__slots__ = ("repos", "name")

	INFOABLE = True

	def __init__(self, parent: typing.Union["GHApiObj", GHAPIBase], name: str, dbID: typing.Optional[int] = None, info: typing.Optional[dict] = None):
		super().__init__(parent, dbID=dbID, info=info)
		self.name = name
		self.repos = None

	def getRepos(self, fresh: bool = False):
		if self.repos is None or fresh:
			repos = {}
			for resReq in self.req("repos", None, method="GET", pagination=slice(None, None)):
				res = resReq.json()
				for el in res:
					repoName = el["name"]
					repos[repoName] = Repo(self.parent, owner=el["owner"]["login"], repo=repoName, dbID=el["id"], info=el)
			self.repos = repos
			return repos
		else:
			return self.repos

	def repo(self, repoName: str, dbID: int = None, info: typing.Optional[dict] = None):
		"""Only sugar. Doesn't populate `repos` prop, as the name can be arbitrary"""

		if self.repos is not None:
			repo = self.repos.get(name, None)
		else:
			repo = None

		if repo is None:
			repo = Repo(self.parent, self.name, repo=repoName, dbID=dbID, info=info)

		return repo


class User(RepoOwner, BlocksMixin):
	__slots__ = ("orgs", "keys")

	def __init__(self, parent, name: str, dbID: typing.Optional[int] = None, info: typing.Optional[dict] = None):
		super().__init__(parent, name, dbID=dbID, info=info)
		self.orgs = None
		self.keys = Keys(self)

	def getOrgs(self, fresh: bool = False):
		if self.orgs is None or fresh:
			orgs = []
			for req in self.req("orgs", None, method="GET", pagination=slice(None, None)):
				for el in req.json():
					orgs.append(Org(self.parent, name=el["login"], dbID=el["id"], info=el))
			self.orgs = orgs
			return orgs
		else:
			return self.orgs

	@property
	def prefix(self) -> str:
		return "users/" + str(self.name) + "/"


class Organization(RepoOwner, BlocksMixin):
	__slots__ = ("actions", "members")

	def __init__(self, parent, name: str, dbID: typing.Optional[int] = None, info: typing.Optional[dict] = None):
		super().__init__(parent, name, dbID=dbID, info=info)
		self.actions = Actions(self)
		self.members = None

	def getMembers(self, fresh: bool = False):
		if self.members is None or fresh:
			members = []
			for req in self.req("members", None, method="GET", pagination=slice(None, None)):
				for el in req.json():
					# el['type']
					members.append(User(self.parent, name=el["login"], dbID=el["id"]))
			self.members = members
			return members
		else:
			return self.members

	@property
	def prefix(self) -> str:
		return "orgs/" + str(self.name) + "/"

	def __repr__(self):
		return self.__class__.__name__ + "<" + repr(self.name) + ", " + repr(self._dbID) + ">"


Org = Organization


class Pages(GHApiObj):
	__slots__ = ()

	@property
	def prefix(self) -> str:
		return "pages/"

	def __init__(self, parent, dbID: int = None, info: typing.Optional[dict] = None):
		super().__init__(parent, dbID=dbID, info=info)

	def delete(self):
		return self.req("", None, method="DELETE")

	def create(self, branch: typing.Optional[str], path: typing.Optional[str] = None, buildType: str = "workflow"):
		o = {}
		if buildType is not None:
			o["build_type"] = buildType

		if branch is not None or path is not None:
			o["source"] = {"branch": branch, "path": path}

		return self.req("", o, method="POST")

	def _deploy(self, url: str, version: str, oidcToken: str, environment: str = "github-pages"):
		"""Docs recommends to set the version to SHA of the commit.
		oidcToken should be got from somewhere within the pipeline env.
		url is the URL to an archive. I guess it can be pipeline-uploaded archive.
		"""

		return self.req("deployment", {"artifact_url": url, "pages_build_version": version, "oidc_token": oidcToken, "environment": environment}, method="POST").json()


def _readmeFallbackProcessor(resp):
	res = resp.json()
	if res["encoding"] == "base64":
		res["$content"] = base64.b64decode(res["content"])
	else:
		res["$content"] = res["content"]

	if isinstance(res["$content"], bytes):
		try:
			res["$content"] = res["$content"].decode("utf-8")
		except:
			pass

	return res


def _readmeRawProcessor(resp):
	return {"$content": resp.text}


def _readmeBase64Processor(resp):
	return {"$content": base64.b64decode(resp.text)}


GET_README_PROCESSORS = {
	CT.json: _readmeFallbackProcessor,
	CT.raw: _readmeRawProcessor,
	CT.html: _readmeRawProcessor,
	CT.raw_base64: _readmeBase64Processor,
}


class Repository(GHApiObj):
	__slots__ = ("owner", "repo", "actions")

	INFOABLE = True

	def __init__(self, parent, owner: str, repo: str, dbID: int = None, info: typing.Optional[dict] = None):
		super().__init__(parent, dbID=dbID, info=info)
		self.owner = owner
		self.repo = repo
		self.actions = Actions(self)

	def _getDBID(self):
		return int(self.gqlReq("query($owner: String!, $repo: String!) {repository(name: $repo, owner: $owner) {databaseId}}", {"owner": parent.owner, "repo": parent.repo, "no": self.no})["data"]["repository"]["databaseId"])

	def ownerObj(self, cls: typing.Union[typing.Type[Org], typing.Type[User]] = User) -> RepoOwner:
		"""Gets an owner object. If the repo metadata dict is populated, the restricted owner data is populated from it.
		It misses some insignificant info:
		* counters: public_repos following followers public_gists
		* social network data: blog name twitter_username email hireable location bio company
		* updates: created_at updated_at
		"""

		if self.info is not None:
			o = self.info["owner"]
			dbID = o["id"]
			login = o["login"]
		else:
			dbID = None
			login = self.owner

		return cls(self.parent, login, dbID, info=self.info["owner"])

	@property
	def prefix(self) -> str:
		return "repos/" + self.owner + "/" + self.repo + "/"

	def issue(self, no: int):
		return Issue(self, no)

	def expell(self, user: str):
		self.req("collaborators/" + user, None, method="DELETE")

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

	def pages(self) -> Pages:
		return Pages(self)

	def getFileRawURL(self, p: PurePosixPath, branch: typing.Optional[str] = None) -> str:
		if branch is None:
			branch = self.info["default_branch"]
			assert branch is not None

		return "https://" + str(PurePosixPath(USERCONTENT_DOMAIN) / self.owner / self.repo / branch / p)

	def getReadMe(self, accept: str = CT.json, path: typing.Optional[PurePosixPath] = None, ref: typing.Optional[str] = None):
		assert accept in GET_README_PROCESSORS
		args = {}
		if ref:
			args["refstring"] = ref

		return GET_README_PROCESSORS[accept](self.req("readme" + (("/" + str(path)) if path is not None else ""), args, method="GET", accept=accept))

	def __repr__(self):
		return self.__class__.__name__ + "<" + repr(self.owner) + ", " + repr(self.repo) + ", " + repr(self._dbID) + ">"


Repo = Repository


ISSUE_COMMENT_SUPPORTED_ACCEPTS = {CT.json, CT.text, CT.html, CT.full}


class Issue(GHApiObj):
	__slots__ = ("no",)

	def __init__(self, parent, no: int, dbID: str = None, info: typing.Optional[dict] = None):
		super().__init__(parent, dbID)
		self.no = no

	def getInfo(self, fresh: bool = False, accept: str = CT.json):
		"""Content is populated into `body`, `body_text` and `body_html` depending on `accept`"""
		assert accept in ISSUE_COMMENT_SUPPORTED_ACCEPTS
		return super().getInfo(fresh=fresh, accept=accept)

	@property
	def prefix(self) -> str:
		return "issues/" + str(self.no) + "/"

	def _getDBID(self):
		return int(self.gqlReq("query($owner: String!, $repo: String!, $no: Int!) {repository(name: $repo, owner: $owner) {issue(number: $no) {databaseId}}}", {"owner": parent.owner, "repo": parent.repo, "no": self.no})["data"]["repository"]["issue"]["databaseId"])

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
		# mutation ($id: ID!) {deleteIssue(input: {issueId: $id}) {clientMutationId}}

	def lock(self, reason: str = None):
		self.req("lock", {"lock_reason": reason} if reason else None, method="put")

	def unlock(self):
		self.req("lock", None, method="DELETE")

	def move(self, repo):
		return self.gqlReq("mutation ($ii: ID!, $ri: ID!) {transferIssue(input: {issueId: $ii, repositoryId: $ri}) {issue{id}}}", {"ii": self.nodeID, "ri": repo.nodeID})

	def react(self, reaction: str):
		self.req("reactions", {"content": reaction}, method="PUT")

	def getEvents(self):
		return self.req("events", previews=("starfox",)).json()


class SSHKeys(GHApiObj):
	__slots__ = ()

	def getSigning(self):
		res = []
		for req in self.parent.req("ssh_signing_keys", None, method="GET", pagination=slice(None, None)):
			res.extend(req.json())
		return res

	@property
	def unlimitedAuthKeysURI(self) -> str:
		return "https://" + MAIN_DOMAIN + "/" + self.parent.name + ".keys"

	def getAuth(self, full: bool = False):
		if full:
			res = []
			for req in self.parent.req("keys", None, method="GET", pagination=slice(None, None)):
				res.extend(req.json())
			return res
		else:
			res = []
			for l in httpx.get(self.unlimitedAuthKeysURI).text.splitlines():
				splitted = l.rsplit(" ")
				if len(splitted) > 2:
					res.append(
						{
							"key": " ".join(splitted[:-1]),
							"title": splitted[-1],
						}
					)
				else:
					res.append({"key": l})
			return res


class Keys(GHApiObj):
	__slots__ = ("ssh",)

	@property
	def unlimitedGPGKeysURI(self) -> str:
		return "https://" + MAIN_DOMAIN + "/" + self.parent.name + ".gpg"

	def getGPGViaAPI(self):
		res = []
		for req in self.parent.req("gpg_keys", None, method="GET", pagination=slice(None, None)):
			res.extend(req.json())
		return res

	def getGPGAsText(self):
		return httpx.get(self.unlimitedGPGKeysURI).text

	def __init__(self, parent):
		super().__init__(parent)
		self.ssh = SSHKeys(self.parent)
