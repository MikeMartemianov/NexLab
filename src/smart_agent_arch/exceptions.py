class LibraryError(Exception):
    """Base exception for all library-level errors."""


class ConfigurationError(LibraryError):
    """Raised for invalid library configuration."""


class ExtensionError(LibraryError):
    """Raised for extension registration or lookup errors."""


class RuntimeStateError(LibraryError):
    """Raised when request processing is attempted in invalid runtime state."""
