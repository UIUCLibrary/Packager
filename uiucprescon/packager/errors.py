"""Custom exceptions."""


class ZipFileException(KeyError):

    def __init__(self, *args: object, zip_file, problem_files=None) -> None:
        self.src_zip_file = zip_file
        self.problem_files = problem_files or []
        super().__init__(*args)
