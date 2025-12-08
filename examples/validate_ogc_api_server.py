"""Example: Validating an OGC API - Features Implementation.

This script demonstrates the complete workflow for validating
an OGC API implementation against the official specifications.

Usage:
    python -m examples.validate_ogc_api_server

Requirements:
    - ogcapi-registry library installed
    - Network access to the target OGC API server
"""

import json
from typing import Any

from ogcapi_registry import (
    ConformanceClass,
    ErrorSeverity,
    OGCAPIType,
    OGCSpecificationKey,
    OGCSpecificationRegistry,
    OpenAPIClient,
    StrategyRegistry,
    ValidationResult,
    get_specification_keys,
    group_conformance_by_spec,
    parse_conformance_classes,
    validate_ogc_api,
)


def fetch_openapi_document(base_url: str) -> dict[str, Any]:
    """Fetch the OpenAPI document from an OGC API server.

    Args:
        base_url: The base URL of the OGC API (e.g., https://demo.ldproxy.net/daraa)

    Returns:
        The parsed OpenAPI document
    """
    client = OpenAPIClient(timeout=30.0)

    # OGC APIs typically serve OpenAPI at /api with format negotiation
    api_url = f"{base_url}/api"

    # Try JSON format first
    try:
        content, metadata = client.fetch(f"{api_url}?f=json")
        return content
    except Exception:
        pass

    # Try with Accept header
    try:
        content, metadata = client.fetch(api_url)
        return content
    except Exception as e:
        raise RuntimeError(f"Failed to fetch OpenAPI document: {e}")


def fetch_conformance_classes(base_url: str) -> list[ConformanceClass]:
    """Fetch conformance classes from the /conformance endpoint.

    Args:
        base_url: The base URL of the OGC API

    Returns:
        List of ConformanceClass objects
    """
    client = OpenAPIClient(timeout=30.0)

    conformance_url = f"{base_url}/conformance?f=json"

    try:
        content, _ = client.fetch(conformance_url)
        return parse_conformance_classes(content)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch conformance: {e}")


def analyze_conformance_coverage(
    conformance_classes: list[ConformanceClass],
) -> dict[str, Any]:
    """Analyze which OGC API specifications and conformance classes are declared.

    Args:
        conformance_classes: List of conformance classes from the server

    Returns:
        Analysis report as a dictionary
    """
    # Group by specification
    spec_groups = group_conformance_by_spec(conformance_classes)

    # Get unique specification keys
    spec_keys = get_specification_keys(conformance_classes)

    # Organize the analysis
    report = {
        "total_conformance_classes": len(conformance_classes),
        "specifications": [],
        "by_api_type": {},
    }

    for key in spec_keys:
        spec_info = {
            "api_type": key.api_type.display_name,
            "version": key.spec_version,
            "part": key.part,
            "key_str": str(key),
            "conformance_classes": [],
        }

        if key in spec_groups:
            for cc in spec_groups[key]:
                spec_info["conformance_classes"].append({
                    "uri": cc.uri,
                    "name": cc.conformance_class_name,
                    "is_core": cc.is_core,
                })

        report["specifications"].append(spec_info)

        # Group by API type
        api_type_name = key.api_type.value
        if api_type_name not in report["by_api_type"]:
            report["by_api_type"][api_type_name] = []
        report["by_api_type"][api_type_name].append(spec_info)

    return report


# Known conformance classes for OGC API - Features Part 1
FEATURES_PART1_CONFORMANCE_CLASSES = {
    "core": "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
    "oas30": "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/oas30",
    "html": "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/html",
    "geojson": "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson",
    "gmlsf0": "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/gmlsf0",
    "gmlsf2": "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/gmlsf2",
}

# Known conformance classes for OGC API - Features Part 2
FEATURES_PART2_CONFORMANCE_CLASSES = {
    "crs": "http://www.opengis.net/spec/ogcapi-features-2/1.0/conf/crs",
}

# Known conformance classes for OGC API - Common Part 1
COMMON_PART1_CONFORMANCE_CLASSES = {
    "core": "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
    "landing-page": "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/landing-page",
    "oas30": "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/oas30",
    "html": "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/html",
    "json": "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/json",
}


def find_missing_conformance_classes(
    declared: list[ConformanceClass],
    known_classes: dict[str, dict[str, str]],
) -> dict[str, list[str]]:
    """Find conformance classes that are not declared by the server.

    Args:
        declared: Conformance classes declared by the server
        known_classes: Dictionary of known conformance classes by spec

    Returns:
        Dictionary mapping spec names to lists of missing class names
    """
    declared_uris = {cc.uri.lower() for cc in declared}

    missing = {}
    for spec_name, classes in known_classes.items():
        spec_missing = []
        for class_name, class_uri in classes.items():
            if class_uri.lower() not in declared_uris:
                spec_missing.append(class_name)
        if spec_missing:
            missing[spec_name] = spec_missing

    return missing


def validate_server(base_url: str) -> dict[str, Any]:
    """Complete validation workflow for an OGC API server.

    Args:
        base_url: The base URL of the OGC API

    Returns:
        Complete validation report
    """
    report = {
        "server_url": base_url,
        "status": "unknown",
        "openapi_document": None,
        "conformance_analysis": None,
        "missing_conformance_classes": None,
        "validation_result": None,
        "errors": [],
        "warnings": [],
    }

    # Step 1: Fetch OpenAPI document
    print(f"Fetching OpenAPI document from {base_url}/api...")
    try:
        openapi_doc = fetch_openapi_document(base_url)
        report["openapi_document"] = {
            "openapi_version": openapi_doc.get("openapi"),
            "title": openapi_doc.get("info", {}).get("title"),
            "version": openapi_doc.get("info", {}).get("version"),
            "paths_count": len(openapi_doc.get("paths", {})),
        }
    except Exception as e:
        report["errors"].append(f"Failed to fetch OpenAPI document: {e}")
        report["status"] = "error"
        return report

    # Step 2: Fetch conformance classes
    print(f"Fetching conformance classes from {base_url}/conformance...")
    try:
        conformance_classes = fetch_conformance_classes(base_url)
        report["conformance_analysis"] = analyze_conformance_coverage(conformance_classes)
    except Exception as e:
        report["errors"].append(f"Failed to fetch conformance: {e}")
        # Continue with validation using path inference

    # Step 3: Identify missing conformance classes
    if conformance_classes:
        known_classes = {
            "OGC API - Features Part 1": FEATURES_PART1_CONFORMANCE_CLASSES,
            "OGC API - Features Part 2": FEATURES_PART2_CONFORMANCE_CLASSES,
            "OGC API - Common Part 1": COMMON_PART1_CONFORMANCE_CLASSES,
        }
        report["missing_conformance_classes"] = find_missing_conformance_classes(
            conformance_classes, known_classes
        )

    # Step 4: Validate the OpenAPI document
    print("Validating OpenAPI document against OGC API specifications...")
    try:
        result = validate_ogc_api(
            openapi_doc,
            conformance_classes if conformance_classes else None,
        )

        # Get error summary by severity
        summary = result.get_summary()

        report["validation_result"] = {
            "is_valid": result.is_valid,
            "is_compliant": result.is_compliant,
            "summary": summary,
            "critical_errors": [dict(e) for e in result.critical_errors],
            "warning_errors": [dict(e) for e in result.warning_errors],
            "info_errors": [dict(e) for e in result.info_errors],
            "warnings": [dict(w) for w in result.warnings],
        }

        # Status based on compliance (not just validity)
        if result.is_valid:
            report["status"] = "valid"
        elif result.is_compliant:
            report["status"] = "compliant"  # No critical errors, but has warnings
        else:
            report["status"] = "non-compliant"  # Has critical errors

    except Exception as e:
        report["errors"].append(f"Validation failed: {e}")
        report["status"] = "error"

    return report


def print_report(report: dict[str, Any]) -> None:
    """Print a formatted validation report."""
    print("\n" + "=" * 60)
    print("OGC API VALIDATION REPORT")
    print("=" * 60)

    print(f"\nServer: {report['server_url']}")
    print(f"Status: {report['status'].upper()}")

    if report["openapi_document"]:
        doc = report["openapi_document"]
        print(f"\nOpenAPI Document:")
        print(f"  Version: {doc['openapi_version']}")
        print(f"  Title: {doc['title']}")
        print(f"  API Version: {doc['version']}")
        print(f"  Paths: {doc['paths_count']}")

    if report["conformance_analysis"]:
        analysis = report["conformance_analysis"]
        print(f"\nConformance Classes: {analysis['total_conformance_classes']}")
        for spec in analysis["specifications"]:
            print(f"\n  {spec['key_str']}:")
            for cc in spec["conformance_classes"]:
                core_marker = " [CORE]" if cc["is_core"] else ""
                print(f"    - {cc['name']}{core_marker}")

    if report["missing_conformance_classes"]:
        print("\nMissing Conformance Classes:")
        for spec, classes in report["missing_conformance_classes"].items():
            print(f"  {spec}:")
            for cls in classes:
                print(f"    - {cls}")

    if report["validation_result"]:
        result = report["validation_result"]
        summary = result.get("summary", {})

        # Display overall status
        if result["is_valid"]:
            print("\nValidation: PASSED (no issues)")
        elif result["is_compliant"]:
            print("\nValidation: COMPLIANT (no critical errors, has warnings)")
        else:
            print("\nValidation: NON-COMPLIANT (has critical errors)")

        # Display summary
        print(f"\n  Summary:")
        print(f"    Critical: {summary.get('critical', 0)}")
        print(f"    Warnings: {summary.get('warning', 0)}")
        print(f"    Info:     {summary.get('info', 0)}")
        print(f"    Total:    {summary.get('total', 0)}")

        # Display critical errors (must fix)
        if result.get("critical_errors"):
            print("\n  CRITICAL ERRORS (must fix for compliance):")
            for error in result["critical_errors"]:
                print(f"    - [{error.get('type', 'error')}] {error.get('message', '')}")

        # Display warning errors (should fix)
        if result.get("warning_errors"):
            print("\n  WARNINGS (optional conformance issues):")
            for error in result["warning_errors"]:
                cc = error.get("conformance_class", "")
                cc_info = f" [{cc.split('/')[-1]}]" if cc else ""
                print(f"    - {error.get('message', '')}{cc_info}")

        # Display info errors (recommendations)
        if result.get("info_errors"):
            print("\n  INFO (recommendations):")
            for error in result["info_errors"]:
                print(f"    - {error.get('message', '')}")

        # Display other warnings
        if result.get("warnings"):
            print("\n  Additional Warnings:")
            for warning in result["warnings"]:
                print(f"    - {warning.get('message', '')}")

    if report["errors"]:
        print("\nProcess Errors:")
        for error in report["errors"]:
            print(f"  - {error}")

    print("\n" + "=" * 60)


# Example with a simulated server response
def demo_with_simulated_data():
    """Demonstrate the workflow with simulated data."""
    print("\n" + "=" * 60)
    print("DEMO: Simulated OGC API - Features Validation")
    print("=" * 60)

    # Simulated OpenAPI document (typical ldproxy response)
    simulated_openapi = {
        "openapi": "3.0.3",
        "info": {
            "title": "Daraa",
            "description": "This is a demo dataset for OGC API - Features",
            "version": "1.0.0",
        },
        "servers": [{"url": "https://demo.ldproxy.net/daraa"}],
        "paths": {
            "/": {"get": {"summary": "Landing page"}},
            "/api": {"get": {"summary": "API definition"}},
            "/conformance": {"get": {"summary": "Conformance classes"}},
            "/collections": {"get": {"summary": "Feature collections"}},
            "/collections/{collectionId}": {"get": {"summary": "Collection info"}},
            "/collections/{collectionId}/items": {
                "get": {"summary": "Features"},
            },
            "/collections/{collectionId}/items/{featureId}": {
                "get": {"summary": "Single feature"},
            },
        },
    }

    # Simulated conformance response (typical ldproxy)
    simulated_conformance = {
        "conformsTo": [
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/oas30",
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/html",
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson",
            "http://www.opengis.net/spec/ogcapi-features-2/1.0/conf/crs",
            "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
            "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/landing-page",
            "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/oas30",
            "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/json",
        ]
    }

    # Parse conformance classes
    conformance_classes = parse_conformance_classes(simulated_conformance)

    print(f"\n1. OpenAPI Document:")
    print(f"   Title: {simulated_openapi['info']['title']}")
    print(f"   Version: {simulated_openapi['openapi']}")
    print(f"   Paths: {len(simulated_openapi['paths'])}")

    print(f"\n2. Declared Conformance Classes ({len(conformance_classes)}):")
    for cc in conformance_classes:
        print(f"   - {cc.conformance_class_name} ({cc.api_type.display_name})")

    # Analyze coverage
    print("\n3. Specification Coverage:")
    spec_keys = get_specification_keys(conformance_classes)
    for key in spec_keys:
        print(f"   - {key}")

    # Find missing conformance classes
    print("\n4. Missing Conformance Classes:")
    known_classes = {
        "OGC API - Features Part 1": FEATURES_PART1_CONFORMANCE_CLASSES,
        "OGC API - Common Part 1": COMMON_PART1_CONFORMANCE_CLASSES,
    }
    missing = find_missing_conformance_classes(conformance_classes, known_classes)
    for spec, classes in missing.items():
        print(f"   {spec}:")
        for cls in classes:
            print(f"     - {cls} (optional)")

    # Validate
    print("\n5. Validation Result:")
    result = validate_ogc_api(simulated_openapi, conformance_classes)

    # Show compliance status (distinguishes critical from non-critical)
    print(f"   Valid: {result.is_valid}")
    print(f"   Compliant: {result.is_compliant}")

    # Show error summary by severity
    summary = result.get_summary()
    print(f"\n   Error Summary:")
    print(f"     Critical: {summary['critical']} (must fix)")
    print(f"     Warnings: {summary['warning']} (optional)")
    print(f"     Info:     {summary['info']} (recommendations)")

    # Show errors by severity level
    if result.critical_errors:
        print("\n   CRITICAL ERRORS:")
        for error in result.critical_errors:
            print(f"     - {error['message']}")

    if result.warning_errors:
        print("\n   WARNINGS:")
        for error in result.warning_errors:
            cc = error.get("conformance_class", "")
            cc_short = cc.split("/")[-1] if cc else ""
            suffix = f" (for {cc_short})" if cc_short else ""
            print(f"     - {error['message']}{suffix}")

    if result.info_errors:
        print("\n   INFO:")
        for error in result.info_errors:
            print(f"     - {error['message']}")

    if result.warnings:
        print("\n   Additional Warnings:")
        for warning in result.warnings:
            print(f"     - {warning['message']}")

    # Version-aware validation
    print("\n6. Version-Aware Validation:")
    strategy_registry = StrategyRegistry()

    detected_keys = strategy_registry.get_detected_spec_keys(
        simulated_openapi, conformance_classes
    )
    print(f"   Detected specifications:")
    for key in detected_keys:
        print(f"     - {key}")


if __name__ == "__main__":
    # Run demo with simulated data
    demo_with_simulated_data()

    # Uncomment to validate a real server:
    # report = validate_server("https://demo.ldproxy.net/daraa")
    # print_report(report)
