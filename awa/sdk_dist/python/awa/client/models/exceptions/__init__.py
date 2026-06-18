class LlmError(Exception):
    pass


class AwaLlmResponseParsingError(Exception):
    pass


class AwaLlmAuthError(LlmError):
    pass


class AwaLlmRateLimitError(LlmError):
    pass


class AwaLlmInvalidRequestError(LlmError):
    pass
