__all__ = ("dbIDAndType2NodeID", "nodeID2DBIDAndType")

import typing
from base64 import b64decode, b64encode


def _dbIDAndType2NodeID(db_id: int, type_name: str) -> str:
	return "0" + str(len(type_name)) + ":" + type_name + str(db_id)


def dbIDAndType2NodeID(db_id: int, type_name: str) -> str:
	return b64encode(_dbIDAndType2NodeID(db_id, type_name).encode("ascii")).decode("ascii")


def _nodeID2DBIDAndType(node_id: str) -> typing.Tuple[int, str]:
	type_len_str, rest = node_id.split(":")
	if not type_len_str or type_len_str[0] != "0":
		raise ValueError("Node ID must start from 0")

	type_len: int = int(type_len_str[1:])
	del type_len_str
	if type_len <= 0:
		raise ValueError("Type length must be natural")

	return int(rest[type_len:]), rest[:type_len]


def nodeID2DBIDAndType(node_id: str) -> typing.Tuple[int, str]:
	return _nodeID2DBIDAndType(b64decode(node_id).decode("ascii"))
