from pathlib import Path


def does_file_exist(path: Path) -> bool:
	"""
	Check whether a file exists on disk.
	"""
	return path.is_file()


def read_file(path: Path) -> str:
	"""
	Load a file and return its contents as a string.
	Raises if the file does not exist.
	"""
	return path.read_text(encoding='utf-8')


def write_file(
	path: Path,
	content: str,
	*,
	mkdir: bool = True,
) -> None:
	"""
	Write text content to a file.

	- Creates parent directories by default
	- Overwrites existing files
	"""
	if mkdir:
		path.parent.mkdir(
			parents=True,
			exist_ok=True,
		)

	path.write_text(
		content,
		encoding='utf-8',
	)
