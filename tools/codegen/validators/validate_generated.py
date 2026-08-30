#!/usr/bin/env python3

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]

REQUIRED = [
    "flutter_app/lib/core/models/authorization.dart",
    "flutter_app/lib/core/models/decision.dart",
    "flutter_app/lib/core/models/device.dart",
    "flutter_app/lib/core/models/entitlement.dart",
    "flutter_app/lib/core/models/evidence.dart",
    "flutter_app/lib/core/models/policy.dart",
    "flutter_app/lib/core/contracts/decision_pipeline_contract.dart",
    "flutter_app/lib/core/contracts/decision_pipeline_result.dart",
    "flutter_app/lib/core/engine/decision_engine.dart",
    "flutter_app/lib/core/services/authorization_service.dart",
    "flutter_app/lib/core/services/entitlement_service.dart",
    "flutter_app/lib/core/services/evidence_service.dart",
    "flutter_app/lib/core/pipeline/decision_pipeline.dart",
    "flutter_app/lib/core/security/security_boundary.dart",
]

def main():
    print("=" * 70)
    print("PHASE 5 GENERATED ARCHITECTURE VALIDATOR")
    print("=" * 70)

    failed = False

    for item in REQUIRED:
        path = ROOT / item

        if path.exists():
            print(f"[PASS] {item}")
        else:
            print(f"[FAIL] {item}")
            failed = True

    if failed:
        print()
        print("VALIDATION FAILED")
        sys.exit(1)

    print()
    print("VALIDATION PASSED")


if __name__ == "__main__":
    main()
