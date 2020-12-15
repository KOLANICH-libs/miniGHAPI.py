try:
	import ujson as json
except ImportError:
	import json

try:
	import httpx
except ImportError:
	import requests as httpx

__all__ = ("httpx", "json", "iterateSlice")


def iterateSlice(slc, defaultStart: int = 0):
	start = slc.start
	stop = slc.stop
	step = slc.step

	if start is None:
		start = defaultStart

	if isinstance(stop, int):
		d = start <= stop
	else:
		d = True

	if step is None:
		step = -1 + 2 * int(d)
	else:
		step = slc.step

	if stop is not None:
		for i in range(start, stop, step):
			yield i
	else:
		i = start
		while True:
			yield i
			i += step
