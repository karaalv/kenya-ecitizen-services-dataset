from pathlib import Path


def delete_file(path: Path) -> None:
	"""
	Delete a file if it exists.

	Intended for test cleanup only.
	"""
	if path.is_file():
		path.unlink()


def delete_dir(path: Path) -> None:
	"""
	Delete a directory tree.

	Intended for test cleanup only.
	"""
	if path.is_dir():
		for p in path.rglob('*'):
			if p.is_file():
				p.unlink()
		for p in sorted(
			path.rglob('*'),
			reverse=True,
		):
			if p.is_dir():
				p.rmdir()
		path.rmdir()
