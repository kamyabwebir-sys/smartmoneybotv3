class IngestionError(Exception):
    """Base error for ingestion-boundary failures."""


class InvalidPayloadError(IngestionError):
    """Raised when evidence does not match the ingestion contract."""


class InvalidDataSchemaError(IngestionError):
    """Raised when provider data cannot be mapped to an ingestion contract."""


class DuplicatePayloadError(IngestionError):
    """Raised when strict ingestion encounters an existing canonical payload."""
