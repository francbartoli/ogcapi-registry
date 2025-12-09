"""Validation strategy for OGC API - Processes."""

from typing import Any, ClassVar

from ..models import ValidationResult
from ..ogc_types import ConformanceClass, OGCAPIType
from .base import ValidationStrategy


class ProcessesStrategy(ValidationStrategy):
    """Validation strategy for OGC API - Processes.

    Validates OpenAPI documents for compliance with the OGC API - Processes
    specification (Part 1: Core).
    """

    api_type: ClassVar[OGCAPIType] = OGCAPIType.PROCESSES
    required_conformance_patterns: ClassVar[list[str]] = [
        "ogcapi-processes",
        "/processes-",
    ]
    optional_conformance_patterns: ClassVar[list[str]] = [
        "/conf/ogc-process-description",
        "/conf/json",
        "/conf/html",
        "/conf/job-list",
        "/conf/dismiss",
        "/conf/callback",
    ]

    def validate(
        self,
        document: dict[str, Any],
        conformance_classes: list[ConformanceClass],
    ) -> ValidationResult:
        """Validate an OpenAPI document for OGC API - Processes compliance.

        Args:
            document: The OpenAPI document to validate
            conformance_classes: Conformance classes declared by the implementation

        Returns:
            ValidationResult with validation outcome
        """
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        # Validate required paths
        required_paths = self.get_required_paths(conformance_classes)
        errors.extend(self.validate_paths_exist(document, required_paths))

        # Validate required operations
        required_ops = self.get_required_operations(conformance_classes)
        errors.extend(self.validate_operations_exist(document, required_ops))

        # Validate processes endpoint
        processes_errors = self._validate_processes_endpoint(document)
        errors.extend(processes_errors)

        # Validate execution endpoint
        execution_errors = self._validate_execution_endpoint(document)
        errors.extend(execution_errors)

        # Validate jobs endpoint if job-list conformance
        if self._has_conformance_class(conformance_classes, "/conf/job-list"):
            jobs_errors = self._validate_jobs_endpoint(document)
            errors.extend(jobs_errors)

        # Validate dismiss if conformance declared
        if self._has_conformance_class(conformance_classes, "/conf/dismiss"):
            dismiss_errors = self._validate_dismiss_support(document)
            errors.extend(dismiss_errors)

        if errors:
            return ValidationResult.failure(errors, warnings=tuple(warnings))

        return ValidationResult.success(warnings=tuple(warnings))

    def get_required_paths(
        self,
        conformance_classes: list[ConformanceClass],
    ) -> list[str]:
        """Get required paths for OGC API - Processes.

        Args:
            conformance_classes: Conformance classes declared by the implementation

        Returns:
            List of required path patterns
        """
        paths = [
            "/",
            "/conformance",
            "/processes",
            "/processes/{processId}",
            "/processes/{processId}/execution",
        ]

        # Jobs list endpoint
        if self._has_conformance_class(conformance_classes, "/conf/job-list"):
            paths.append("/jobs")

        # Job status endpoint (always required for async)
        paths.append("/jobs/{jobId}")

        # Job results endpoint
        paths.append("/jobs/{jobId}/results")

        return paths

    def get_required_operations(
        self,
        conformance_classes: list[ConformanceClass],
    ) -> dict[str, list[str]]:
        """Get required operations for OGC API - Processes paths.

        Args:
            conformance_classes: Conformance classes declared by the implementation

        Returns:
            Dict mapping paths to required HTTP methods
        """
        operations: dict[str, list[str]] = {
            "/": ["get"],
            "/conformance": ["get"],
            "/processes": ["get"],
            "/processes/{processId}": ["get"],
            "/processes/{processId}/execution": ["post"],
            "/jobs/{jobId}": ["get"],
            "/jobs/{jobId}/results": ["get"],
        }

        if self._has_conformance_class(conformance_classes, "/conf/job-list"):
            operations["/jobs"] = ["get"]

        if self._has_conformance_class(conformance_classes, "/conf/dismiss"):
            operations["/jobs/{jobId}"] = ["get", "delete"]

        return operations

    def _validate_processes_endpoint(
        self, document: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Validate the processes list endpoint.

        Args:
            document: The OpenAPI document

        Returns:
            List of validation errors
        """
        errors: list[dict[str, Any]] = []
        paths = document.get("paths", {})

        processes = paths.get("/processes", {})
        get_op = processes.get("get", {})

        if not get_op:
            return errors

        responses = get_op.get("responses", {})
        if "200" not in responses and "2XX" not in responses:
            errors.append(
                {
                    "path": "paths//processes.get.responses",
                    "message": "Processes GET should have a 200 response",
                    "type": "missing_response",
                }
            )

        return errors

    def _validate_execution_endpoint(
        self, document: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Validate the execution endpoint.

        Args:
            document: The OpenAPI document

        Returns:
            List of validation errors
        """
        errors: list[dict[str, Any]] = []
        paths = document.get("paths", {})

        # Find execution path
        execution_path = None
        for path in paths:
            if "/execution" in path and "{processId}" in path:
                execution_path = path
                break

        if not execution_path:
            return errors

        post_op = paths[execution_path].get("post", {})
        if not post_op:
            return errors

        responses = post_op.get("responses", {})

        # Should have 200 (sync) or 201 (async) response
        has_success = any(code in responses for code in ["200", "201", "2XX"])
        if not has_success:
            errors.append(
                {
                    "path": f"paths/{execution_path}.post.responses",
                    "message": "Execution POST should have 200 (sync) or 201 (async) response",
                    "type": "missing_response",
                }
            )

        # Check for request body
        if "requestBody" not in post_op:
            errors.append(
                {
                    "path": f"paths/{execution_path}.post",
                    "message": "Execution POST should have a requestBody for process inputs",
                    "type": "missing_request_body",
                }
            )

        return errors

    def _validate_jobs_endpoint(self, document: dict[str, Any]) -> list[dict[str, Any]]:
        """Validate the jobs list endpoint.

        Args:
            document: The OpenAPI document

        Returns:
            List of validation errors
        """
        errors: list[dict[str, Any]] = []
        paths = document.get("paths", {})

        jobs = paths.get("/jobs", {})
        get_op = jobs.get("get", {})

        if not get_op:
            return errors

        responses = get_op.get("responses", {})
        if "200" not in responses and "2XX" not in responses:
            errors.append(
                {
                    "path": "paths//jobs.get.responses",
                    "message": "Jobs GET should have a 200 response",
                    "type": "missing_response",
                }
            )

        return errors

    def _validate_dismiss_support(
        self, document: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Validate dismiss (DELETE job) support.

        Args:
            document: The OpenAPI document

        Returns:
            List of validation errors
        """
        errors: list[dict[str, Any]] = []
        paths = document.get("paths", {})

        # Find job status path
        job_path = None
        for path in paths:
            if "/jobs/" in path and "{jobId}" in path and "results" not in path:
                job_path = path
                break

        if not job_path:
            return errors

        delete_op = paths[job_path].get("delete", {})
        if not delete_op:
            errors.append(
                {
                    "path": f"paths/{job_path}",
                    "message": "Dismiss conformance requires DELETE operation on job endpoint",
                    "type": "missing_operation",
                }
            )
            return errors

        responses = delete_op.get("responses", {})
        has_success = any(code in responses for code in ["200", "204", "2XX"])
        if not has_success:
            errors.append(
                {
                    "path": f"paths/{job_path}.delete.responses",
                    "message": "Job DELETE should have 200 or 204 response",
                    "type": "missing_response",
                }
            )

        return errors

    @staticmethod
    def _has_conformance_class(
        conformance_classes: list[ConformanceClass],
        pattern: str,
    ) -> bool:
        """Check if a conformance class matching the pattern exists."""
        pattern_lower = pattern.lower()
        return any(pattern_lower in cc.uri.lower() for cc in conformance_classes)
