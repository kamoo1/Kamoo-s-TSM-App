class AHError(Exception):
    """Base class for exceptions in this module."""

    pass


class DownloadError(AHError):
    pass


class CompressTsError(ValueError, AHError):
    pass
