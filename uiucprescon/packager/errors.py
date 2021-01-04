"""Custom exceptions."""


class ZipFileException(KeyError):

    def __init__(self, *args: object, zip_file, problem_files=None) -> None:
        """ZipFileException.

        Args:
            *args:
            zip_file: Source zip containing the problem
            problem_files:
                Optional: problematic files associated with this error
        """
        self.src_zip_file = zip_file
        self.problem_files = problem_files or []
        super().__init__(*args)
