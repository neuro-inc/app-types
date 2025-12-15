"""Filter module for dynamic output filtering.

Provides common filter types and utilities for filtering dynamic app outputs.
Applications can import base types and extend BaseModelFilter for app-specific
filtering logic.

Filter syntax: field:operator:value,field2:operator2:value2

Supported operators:
    - eq: Exact match (case-insensitive)
    - ne: Not equal (case-insensitive)
    - like: Contains substring (case-insensitive)
    - in: Value exists in list field

Examples:
    - name:eq:my-model
    - name:like:llama
    - tags:in:production
"""

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, TypeVar

from pydantic import BaseModel


logger = logging.getLogger(__name__)

T = TypeVar("T")


class FilterOperator(Enum):
    """Supported filter operators."""

    EQ = "eq"
    NE = "ne"
    LIKE = "like"
    IN = "in"


class FilterCondition(BaseModel):
    """A single filter condition."""

    field: str
    operator: FilterOperator
    value: str


def parse_filter_string(filter_string: str) -> list[FilterCondition]:
    """Parse filter string into conditions.

    Args:
        filter_string: Filter string in format field:op:value,field:op:value

    Returns:
        List of parsed FilterCondition objects
    """
    conditions: list[FilterCondition] = []
    for part in filter_string.split(","):
        part = part.strip()
        if not part:
            continue

        parts = part.split(":")
        if len(parts) == 3:
            field, op, value = parts
            try:
                operator = FilterOperator(op.lower())
                conditions.append(
                    FilterCondition(field=field.lower(), operator=operator, value=value)
                )
            except ValueError:
                err_msg = f"Unknown filter operator: {op}"
                logger.warning(err_msg)
        else:
            err_msg = f"Invalid filter format: {part}. Expected field:operator:value"
            logger.warning(err_msg)
    return conditions


def compare_equal(value: Any, filter_value: str) -> bool:
    """Compare value for equality, handling different types.

    Args:
        value: Model field value
        filter_value: Filter value (string)

    Returns:
        True if values are equal
    """
    if isinstance(value, bool):
        return str(value).lower() == filter_value.lower()
    if isinstance(value, int | float):
        try:
            return value == type(value)(filter_value)
        except (ValueError, TypeError):
            return False
    return str(value).lower() == filter_value.lower()


def compare_like(value: Any, filter_value: str) -> bool:
    """Check if filter_value is a substring of value.

    Args:
        value: Model field value
        filter_value: Substring to search for

    Returns:
        True if filter_value is found in value
    """
    return filter_value.lower() in str(value).lower()


class BaseModelFilter(ABC):
    """Base filter class with common parsing and comparison logic.

    Subclasses must implement:
    - _get_field_value(): How to extract field values from model
    - _matches_in_operator(): How to handle IN operator for list fields

    Example usage::

        class ModelFilter(BaseModelFilter):
            def _get_field_value(self, model, field):
                return model.get(field)  # For dict models

            def _matches_in_operator(self, value, filter_value):
                if isinstance(value, list):
                    return any(filter_value.lower() == v.lower() for v in value)
                return False

        # Use the filter
        model_filter = ModelFilter("name:like:llama,tags:in:production")
        filtered = model_filter.apply(models)
    """

    def __init__(self, filter_string: str | None) -> None:
        """Initialize filter from filter string.

        Args:
            filter_string: Filter string in format field:op:value,field:op:value
        """
        self.conditions: list[FilterCondition] = []
        self._raw_filter = filter_string

        if filter_string:
            self.conditions = parse_filter_string(filter_string)

    def apply(self, models: list[T]) -> list[T]:
        """Apply all filter conditions to a list of models.

        Args:
            models: List of models to filter

        Returns:
            Filtered list of models matching all conditions (AND logic)
        """
        if not self.conditions:
            return models

        result = models
        for condition in self.conditions:
            result = [m for m in result if self._matches(m, condition)]
        debug_msg = f"Filter applied: {len(models)} -> {len(result)} models"
        logger.debug(
            debug_msg,
            extra={"conditions": len(self.conditions)},
        )
        return result

    def _matches(self, model: T, condition: FilterCondition) -> bool:
        """Check if a model matches a single filter condition.

        Args:
            model: Model to check
            condition: Filter condition to apply

        Returns:
            True if model matches the condition
        """
        value = self._get_field_value(model, condition.field)

        if value is None:
            return condition.operator == FilterOperator.NE

        match condition.operator:
            case FilterOperator.EQ:
                return compare_equal(value, condition.value)
            case FilterOperator.NE:
                return not compare_equal(value, condition.value)
            case FilterOperator.LIKE:
                return compare_like(value, condition.value)
            case FilterOperator.IN:
                return self._matches_in_operator(value, condition.value)

        return False

    @abstractmethod
    def _get_field_value(self, model: T, field: str) -> Any:
        """Get field value from model. Override for app-specific access.

        Args:
            model: Model to extract field from
            field: Field name to retrieve

        Returns:
            Field value or None if not found
        """
        ...

    @abstractmethod
    def _matches_in_operator(self, value: Any, filter_value: str) -> bool:
        """Handle IN operator. Override for app-specific list structures.

        Args:
            value: Field value (expected to be a list)
            filter_value: Value to search for in the list

        Returns:
            True if filter_value is found in value
        """
        ...

    def has_conditions(self) -> bool:
        """Check if filter has any conditions to apply.

        Returns:
            True if there are conditions
        """
        return bool(self.conditions)

    def __repr__(self) -> str:
        """String representation of filter."""
        return f"{self.__class__.__name__}(conditions={len(self.conditions)})"
