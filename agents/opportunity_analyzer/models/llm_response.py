from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class LLMResponseStatus(str, Enum):
    OK = "ok"
    PARSE_FAILED = "parse_failed"
    EMPTY = "empty"
    ERROR = "error"


@dataclass
class LLMResponse:
    """
    Wraps every LLM call. Small models fail in specific, boring ways
    (malformed JSON, empty output, wrapped-in-prose output) — this
    model makes those failure states explicit rather than letting
    a caller assume `data` is always trustworthy.
    """

    status: LLMResponseStatus
    data: dict[str, Any] = field(default_factory=dict)
    raw_text: str = ""
    prompt_name: str = ""
    attempts: int = 1
    error: Optional[str] = None

    def __post_init__(self) -> None:
        """Sanitize strings and guarantee enum typing."""
        if isinstance(self.status, str) and not isinstance(self.status, LLMResponseStatus):
            self.status = LLMResponseStatus(self.status)

        self.raw_text = self.raw_text.strip() if self.raw_text else ""
        self.prompt_name = self.prompt_name.strip() if self.prompt_name else ""
        if self.error:
            self.error = self.error.strip()

    @property
    def is_usable(self) -> bool:
        """True only if status is OK and non-empty data was extracted."""
        return self.status == LLMResponseStatus.OK and bool(self.data)

    @property
    def has_error(self) -> bool:
        """True if status is an error/failed state or an error message exists."""
        return self.status != LLMResponseStatus.OK or bool(self.error)

    def validate(self) -> list[str]:
        """Returns a list of validation errors, empty if valid."""
        errors: list[str] = []

        # 1. Negative or zero attempt count
        if self.attempts < 1:
            errors.append(f"LLMResponse.attempts must be >= 1 (got {self.attempts}).")

        # 2. Status vs. Payload Consistency
        if self.status == LLMResponseStatus.OK and not self.data:
            errors.append("LLMResponse.status is 'ok' but 'data' dictionary is empty.")

        if self.status == LLMResponseStatus.EMPTY and self.data:
            errors.append("LLMResponse.status is 'empty' but 'data' contains values.")

        # 3. Status vs. Error Message Consistency
        if self.status in (LLMResponseStatus.ERROR, LLMResponseStatus.PARSE_FAILED) and not self.error:
            errors.append(f"LLMResponse.status is '{self.status.value}' but no error message was provided.")

        return errors

    @property
    def is_valid(self) -> bool:
        """Helper to quickly check if response object state is self-consistent."""
        return len(self.validate()) == 0

    @classmethod
    def fail(
        cls,
        status: LLMResponseStatus,
        error: str,
        prompt_name: str = "",
        raw_text: str = "",
        attempts: int = 1,
    ) -> "LLMResponse":
        """Factory method to construct explicit failure responses."""
        return cls(
            status=status,
            data={},
            raw_text=raw_text,
            prompt_name=prompt_name,
            attempts=attempts,
            error=error,
        )