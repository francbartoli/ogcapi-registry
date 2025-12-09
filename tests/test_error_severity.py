"""Tests for ErrorSeverity and ValidationResult severity filtering."""

from ogcapi_registry import (
    ErrorSeverity,
    ValidationResult,
    FeaturesStrategy,
    ConformanceClass,
)


class TestErrorSeverity:
    """Tests for ErrorSeverity enum."""

    def test_severity_values(self) -> None:
        """Test that severity enum has expected values."""
        assert ErrorSeverity.CRITICAL.value == "critical"
        assert ErrorSeverity.WARNING.value == "warning"
        assert ErrorSeverity.INFO.value == "info"

    def test_severity_is_string_enum(self) -> None:
        """Test that severity enum values are strings."""
        assert isinstance(ErrorSeverity.CRITICAL.value, str)
        # str(Enum) includes class name, but .value gives the string value
        assert ErrorSeverity.CRITICAL.value == "critical"


class TestValidationResultSeverity:
    """Tests for ValidationResult severity filtering methods."""

    def test_get_errors_by_severity_critical(self) -> None:
        """Test filtering errors by CRITICAL severity."""
        errors = [
            {"message": "critical error 1", "severity": "critical"},
            {"message": "warning error 1", "severity": "warning"},
            {"message": "critical error 2", "severity": "critical"},
            {"message": "info error 1", "severity": "info"},
        ]
        result = ValidationResult.failure(errors)

        critical = result.get_errors_by_severity(ErrorSeverity.CRITICAL)
        assert len(critical) == 2
        assert all(e["severity"] == "critical" for e in critical)

    def test_get_errors_by_severity_warning(self) -> None:
        """Test filtering errors by WARNING severity."""
        errors = [
            {"message": "critical error 1", "severity": "critical"},
            {"message": "warning error 1", "severity": "warning"},
            {"message": "warning error 2", "severity": "warning"},
        ]
        result = ValidationResult.failure(errors)

        warnings = result.get_errors_by_severity(ErrorSeverity.WARNING)
        assert len(warnings) == 2
        assert all(e["severity"] == "warning" for e in warnings)

    def test_get_errors_by_severity_info(self) -> None:
        """Test filtering errors by INFO severity."""
        errors = [
            {"message": "critical error 1", "severity": "critical"},
            {"message": "info error 1", "severity": "info"},
        ]
        result = ValidationResult.failure(errors)

        info = result.get_errors_by_severity(ErrorSeverity.INFO)
        assert len(info) == 1
        assert info[0]["severity"] == "info"

    def test_critical_errors_property(self) -> None:
        """Test the critical_errors property."""
        errors = [
            {"message": "critical", "severity": "critical"},
            {"message": "warning", "severity": "warning"},
        ]
        result = ValidationResult.failure(errors)

        assert len(result.critical_errors) == 1
        assert result.critical_errors[0]["message"] == "critical"

    def test_warning_errors_property(self) -> None:
        """Test the warning_errors property."""
        errors = [
            {"message": "critical", "severity": "critical"},
            {"message": "warning", "severity": "warning"},
        ]
        result = ValidationResult.failure(errors)

        assert len(result.warning_errors) == 1
        assert result.warning_errors[0]["message"] == "warning"

    def test_info_errors_property(self) -> None:
        """Test the info_errors property."""
        errors = [
            {"message": "info", "severity": "info"},
            {"message": "warning", "severity": "warning"},
        ]
        result = ValidationResult.failure(errors)

        assert len(result.info_errors) == 1
        assert result.info_errors[0]["message"] == "info"

    def test_has_critical_errors_true(self) -> None:
        """Test has_critical_errors when critical errors exist."""
        errors = [
            {"message": "critical", "severity": "critical"},
            {"message": "warning", "severity": "warning"},
        ]
        result = ValidationResult.failure(errors)

        assert result.has_critical_errors is True

    def test_has_critical_errors_false(self) -> None:
        """Test has_critical_errors when no critical errors exist."""
        errors = [
            {"message": "warning", "severity": "warning"},
            {"message": "info", "severity": "info"},
        ]
        result = ValidationResult.failure(errors)

        assert result.has_critical_errors is False

    def test_is_compliant_with_no_critical_errors(self) -> None:
        """Test is_compliant is True when no critical errors."""
        errors = [
            {"message": "warning", "severity": "warning"},
            {"message": "info", "severity": "info"},
        ]
        result = ValidationResult.failure(errors)

        # is_valid is False (has errors), but is_compliant is True (no critical errors)
        assert result.is_valid is False
        assert result.is_compliant is True

    def test_is_compliant_with_critical_errors(self) -> None:
        """Test is_compliant is False when critical errors exist."""
        errors = [
            {"message": "critical", "severity": "critical"},
        ]
        result = ValidationResult.failure(errors)

        assert result.is_valid is False
        assert result.is_compliant is False

    def test_is_compliant_success(self) -> None:
        """Test is_compliant is True for successful validation."""
        result = ValidationResult.success()

        assert result.is_valid is True
        assert result.is_compliant is True

    def test_get_summary(self) -> None:
        """Test get_summary returns correct counts."""
        errors = [
            {"message": "critical 1", "severity": "critical"},
            {"message": "critical 2", "severity": "critical"},
            {"message": "warning 1", "severity": "warning"},
            {"message": "info 1", "severity": "info"},
            {"message": "info 2", "severity": "info"},
            {"message": "info 3", "severity": "info"},
        ]
        result = ValidationResult.failure(errors)

        summary = result.get_summary()
        assert summary["critical"] == 2
        assert summary["warning"] == 1
        assert summary["info"] == 3
        assert summary["total"] == 6

    def test_get_summary_empty(self) -> None:
        """Test get_summary with no errors."""
        result = ValidationResult.success()

        summary = result.get_summary()
        assert summary["critical"] == 0
        assert summary["warning"] == 0
        assert summary["info"] == 0
        assert summary["total"] == 0

    def test_errors_without_severity_not_filtered(self) -> None:
        """Test that errors without severity field are not included in filtered results."""
        errors = [
            {"message": "critical", "severity": "critical"},
            {"message": "no severity"},  # No severity field
        ]
        result = ValidationResult.failure(errors)

        assert len(result.critical_errors) == 1
        assert len(result.warning_errors) == 0
        assert len(result.info_errors) == 0
        # Total includes the error without severity
        assert result.get_summary()["total"] == 2


class TestStrategyErrorSeverity:
    """Tests for error severity in validation strategies."""

    def test_features_strategy_critical_errors(self) -> None:
        """Test that FeaturesStrategy produces critical errors for missing required paths."""
        strategy = FeaturesStrategy()
        document = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/": {"get": {"responses": {"200": {"description": "OK"}}}},
            },
        }
        conformance = [
            ConformanceClass(
                uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"
            ),
        ]

        result = strategy.validate(document, conformance)

        assert not result.is_valid
        # Missing paths should be critical
        assert len(result.critical_errors) > 0

    def test_features_strategy_warning_for_optional_bbox(self) -> None:
        """Test that missing bbox parameter is a warning, not critical."""
        strategy = FeaturesStrategy()
        # Document with required paths but missing bbox parameter
        document = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/": {"get": {"responses": {"200": {"description": "OK"}}}},
                "/conformance": {"get": {"responses": {"200": {"description": "OK"}}}},
                "/collections": {"get": {"responses": {"200": {"description": "OK"}}}},
                "/collections/{collectionId}": {
                    "get": {"responses": {"200": {"description": "OK"}}}
                },
                "/collections/{collectionId}/items": {
                    "get": {
                        "parameters": [
                            {"name": "limit", "in": "query"},
                            # bbox is missing - should be warning
                        ],
                        "responses": {"200": {"description": "OK"}},
                    }
                },
                "/collections/{collectionId}/items/{featureId}": {
                    "get": {"responses": {"200": {"description": "OK"}}}
                },
            },
        }
        conformance = [
            ConformanceClass(
                uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"
            ),
        ]

        result = strategy.validate(document, conformance)

        # Find the bbox warning
        bbox_errors = [e for e in result.errors if "bbox" in e.get("message", "")]
        assert len(bbox_errors) == 1
        assert bbox_errors[0]["severity"] == "warning"

    def test_features_strategy_crs_warnings(self) -> None:
        """Test that CRS conformance errors are warnings (optional conformance)."""
        strategy = FeaturesStrategy()
        document = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/": {"get": {"responses": {"200": {"description": "OK"}}}},
                "/conformance": {"get": {"responses": {"200": {"description": "OK"}}}},
                "/collections": {"get": {"responses": {"200": {"description": "OK"}}}},
                "/collections/{collectionId}": {
                    "get": {"responses": {"200": {"description": "OK"}}}
                },
                "/collections/{collectionId}/items": {
                    "get": {
                        "parameters": [
                            {"name": "limit", "in": "query"},
                            {"name": "bbox", "in": "query"},
                            # crs and bbox-crs are missing
                        ],
                        "responses": {"200": {"description": "OK"}},
                    }
                },
                "/collections/{collectionId}/items/{featureId}": {
                    "get": {"responses": {"200": {"description": "OK"}}}
                },
            },
        }
        conformance = [
            ConformanceClass(
                uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"
            ),
            ConformanceClass(
                uri="http://www.opengis.net/spec/ogcapi-features-2/1.0/conf/crs"
            ),
        ]

        result = strategy.validate(document, conformance)

        # CRS errors should be warnings
        crs_errors = [e for e in result.errors if "crs" in e.get("message", "").lower()]
        assert len(crs_errors) >= 1
        for error in crs_errors:
            assert error["severity"] == "warning"
            assert "conformance_class" in error

    def test_features_strategy_filter_info(self) -> None:
        """Test that filter conformance warnings are INFO level."""
        strategy = FeaturesStrategy()
        document = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/": {"get": {"responses": {"200": {"description": "OK"}}}},
                "/conformance": {"get": {"responses": {"200": {"description": "OK"}}}},
                "/collections": {"get": {"responses": {"200": {"description": "OK"}}}},
                "/collections/{collectionId}": {
                    "get": {"responses": {"200": {"description": "OK"}}}
                },
                "/collections/{collectionId}/items": {
                    "get": {
                        "parameters": [
                            {"name": "limit", "in": "query"},
                            {"name": "bbox", "in": "query"},
                            # filter and filter-lang are missing
                        ],
                        "responses": {"200": {"description": "OK"}},
                    }
                },
                "/collections/{collectionId}/items/{featureId}": {
                    "get": {"responses": {"200": {"description": "OK"}}}
                },
            },
        }
        conformance = [
            ConformanceClass(
                uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"
            ),
            ConformanceClass(
                uri="http://www.opengis.net/spec/ogcapi-features-3/1.0/conf/filter"
            ),
        ]

        result = strategy.validate(document, conformance)

        # Filter warnings should be INFO level (in the warnings tuple)
        filter_warnings = [
            w for w in result.warnings if "filter" in w.get("message", "").lower()
        ]
        assert len(filter_warnings) >= 1
        for warning in filter_warnings:
            assert warning["severity"] == "info"
            assert "conformance_class" in warning


class TestComplianceVsValidity:
    """Tests for the distinction between is_valid and is_compliant."""

    def test_compliant_but_not_valid(self) -> None:
        """Test a document can be compliant (no critical) but not valid (has warnings)."""
        errors = [
            {"message": "warning 1", "severity": "warning"},
            {"message": "info 1", "severity": "info"},
        ]
        result = ValidationResult.failure(errors)

        # Not valid because it has errors
        assert result.is_valid is False
        # But compliant because no critical errors
        assert result.is_compliant is True
        assert result.has_critical_errors is False

    def test_neither_compliant_nor_valid(self) -> None:
        """Test a document with critical errors is neither compliant nor valid."""
        errors = [
            {"message": "critical 1", "severity": "critical"},
            {"message": "warning 1", "severity": "warning"},
        ]
        result = ValidationResult.failure(errors)

        assert result.is_valid is False
        assert result.is_compliant is False
        assert result.has_critical_errors is True

    def test_both_compliant_and_valid(self) -> None:
        """Test a successful validation is both compliant and valid."""
        result = ValidationResult.success()

        assert result.is_valid is True
        assert result.is_compliant is True
        assert result.has_critical_errors is False
