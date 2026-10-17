"""Exceptions raised by the code-analysis agent."""


class CodeAnalysisError(ValueError):
    """Raised when submitted source cannot be analyzed safely."""


class UnsupportedLanguageError(CodeAnalysisError):
    """Raised when a requested language is not supported by any analyzer."""
