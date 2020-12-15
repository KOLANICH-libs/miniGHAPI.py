import argparse
from pathlib import Path, PurePath


def uploadArtifact(args):
	args.file = [Path(el) for el in args.file]
	if args.name:
		args.name = [PurePath(el) for el in args.name.split(":")]
		if len(args.name) != len(args.file):
			raise ValueError("Count of names for files must match count of files")
	else:
		args.name = [None] * len(args.file)

	if args.containerName is None:
		if len(args.name) == 1:
			if args.name[0]:
				args.containerName = args.name[0].name
			else:
				args.containerName = args.file[0].name
		else:
			raise ValueError("You must provide container name when dealing with multiple files")

	from .GHActionsEnv import getGHEnv
	from .undocumented import PipelinesAPIRoot

	env = getGHEnv()

	pu = PipelinesAPIRoot(env["ACTIONS"]["RUNTIME_TOKEN"], "miniGHApi", env=env)

	def uploadSubTree(u, filePath, prefix):
		if filePath.is_dir():
			for el in filePath.iterdir():
				uploadSubTree(u, el, prefix / el.name)
		else:
			u[prefix] = filePath.read_bytes()

	with pu.pipelines.getArtifactUploader(args.containerName) as u:
		for name, filePath in zip(args.name, args.file):
			uploadSubTree(u, filePath, name)


def uploadCache(args):
	pass


def main():
	parser = argparse.ArgumentParser(description="CLI tool to work with some GitHub API")
	subparsers = parser.add_subparsers()

	artifact = subparsers.add_parser("artifact")
	artifact.add_argument("--containerName", "-C", type=str, help="Name of the container")
	artifact.add_argument("--name", type=str, help="Name of the file")
	artifact.add_argument("file", type=str, nargs="+", help="Path to a file to upload")
	artifact.set_defaults(func=uploadArtifact)

	#cache = subparsers.add_parser("cache")
	#cache.add_argument("dir", type=str, nargs="+", help="Path of file to upload")
	#cache.set_defaults(func=uploadCache)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
