"""Custom exceptions."""
from typing import Optional, List


class ZipFileException(KeyError):
    """Problem with the zip file or the files contained in the zip file."""

    def __init__(
            self,
            *args: object,
            zip_file: str,
            problem_files:
            Optional[List[str]] = None
    ) -> None:
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
