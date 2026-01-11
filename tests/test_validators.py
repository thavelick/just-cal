"""Tests for validators module."""

from datetime import datetime

import pytest

from just_cal.utils.validators import validate_date_range, validate_non_empty


class TestValidateDateRange:
    """Tests for validate_date_range function."""

    def test_validate_date_range_valid(self):
        """Test validation passes when end is after start."""
        start = datetime(2026, 1, 15, 10, 0, 0)
        end = datetime(2026, 1, 15, 11, 0, 0)
        # Should not raise
        validate_date_range(start, end)

    def test_validate_date_range_same_time(self):
        """Test validation passes when start and end are the same."""
        start = datetime(2026, 1, 15, 10, 0, 0)
        end = datetime(2026, 1, 15, 10, 0, 0)
        # Should not raise (equal times are allowed)
        validate_date_range(start, end)

    def test_validate_date_range_invalid(self):
        """Test validation fails when end is before start."""
        start = datetime(2026, 1, 15, 11, 0, 0)
        end = datetime(2026, 1, 15, 10, 0, 0)
        with pytest.raises(ValueError, match="End date .* cannot be before start date"):
            validate_date_range(start, end)

    def test_validate_date_range_different_days(self):
        """Test validation with dates on different days."""
        start = datetime(2026, 1, 15, 10, 0, 0)
        end = datetime(2026, 1, 16, 10, 0, 0)
        # Should not raise
        validate_date_range(start, end)


class TestValidateNonEmpty:
    """Tests for validate_non_empty function."""

    def test_validate_non_empty_valid(self):
        """Test validation passes with non-empty string."""
        validate_non_empty("Team Meeting", "Title")

    def test_validate_non_empty_empty_string(self):
        """Test validation fails with empty string."""
        with pytest.raises(ValueError, match="Title cannot be empty"):
            validate_non_empty("", "Title")

    def test_validate_non_empty_whitespace_only(self):
        """Test validation fails with whitespace-only string."""
        with pytest.raises(ValueError, match="Description cannot be empty"):
            validate_non_empty("   ", "Description")

    def test_validate_non_empty_with_spaces(self):
        """Test validation passes with string containing spaces."""
        validate_non_empty("  Valid Title  ", "Title")

    def test_validate_non_empty_custom_field_name(self):
        """Test error message uses custom field name."""
        with pytest.raises(ValueError, match="Location cannot be empty"):
            validate_non_empty("", "Location")
