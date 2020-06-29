class ZipFileException(KeyError):

    def __init__(self, *args: object, src) -> None:
        self.src = src
        super().__init__(*args)
