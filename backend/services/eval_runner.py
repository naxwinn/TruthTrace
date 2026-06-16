"""
Evaluation Test Runner
Runs the analysis pipeline against all test cases and verifies expected detections.
"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database import engine, Base, SessionLocal
from api.models import MediaFile, AnalysisJob, Finding
from services.analysis_pipeline import AnalysisPipeline
from services.eval_dataset import generate_all_test_cases

TEST_DATA_DIR = Path(__file__).parent.parent / "test_data"


# Expected detections for each test case
EXPECTED = {
    "test1_trimmed.mp4": {
        "description": "2 seconds removed from middle",
        "must_detect": ["compression_anomaly", "gop_break", "frame_deletion"],
        "should_detect_any": True,
    },
    "test2_audio_splice.mp4": {
        "description": "1 second of audio removed",
        "must_detect": ["audio_splice", "mfcc_discontinuity"],
        "should_detect_any": True,
    },
    "test3_synthetic_voice.mp4": {
        "description": "Synthetic tone inserted at 2s-4s",
        "must_detect": ["audio_splice", "synthetic_voice"],
        "should_detect_any": True,
    },
}


def run_evaluation():
    """Run full evaluation suite."""
    print("=" * 70)
    print("TruthTrace Evaluation Suite")
    print("=" * 70)

    # Generate test data if needed
    missing = [f for f in EXPECTED.keys() if not (TEST_DATA_DIR / f).exists()]
    if missing:
        print(f"\nGenerating missing test files: {missing}")
        generate_all_test_cases()

    # Create fresh DB
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    results = {}
    total_pass = 0
    total_fail = 0

    for filename, expected in EXPECTED.items():
        filepath = TEST_DATA_DIR / filename
        if not filepath.exists():
            print(f"\n[SKIP] {filename} - file not found")
            continue

        print(f"\n{'─' * 70}")
        print(f"[TEST] {filename}")
        print(f"       {expected['description']}")
        print(f"       Expected: {expected['must_detect']}")
        print(f"{'─' * 70}")

        # Create records
        file_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())

        media = MediaFile(
            id=file_id,
            filename=filename,
            original_filename=filename,
            file_path=str(filepath),
            file_size=filepath.stat().st_size,
            mime_type="video/mp4",
        )
        db.add(media)

        job = AnalysisJob(id=job_id, media_file_id=file_id)
        db.add(job)
        db.commit()

        # Run pipeline
        print("       Running analysis pipeline...")
        pipeline = AnalysisPipeline(job_id)
        pipeline.run()

        # Check results
        db.refresh(job)
        findings = db.query(Finding).filter(Finding.job_id == job_id).all()
        finding_types = set(f.finding_type for f in findings)
        detector_types = set(f.detector_type for f in findings)

        print(f"       Status: {job.status}")
        print(f"       Authenticity score: {job.authenticity_score}")
        print(f"       Findings: {len(findings)}")
        print(f"       Types found: {finding_types}")
        print(f"       Detectors: {detector_types}")

        # Evaluate
        detected = []
        missed = []
        for expected_type in expected["must_detect"]:
            if expected_type in finding_types:
                detected.append(expected_type)
            else:
                missed.append(expected_type)

        passed = len(detected) > 0 if expected["should_detect_any"] else len(missed) == 0
        full_pass = len(missed) == 0

        if full_pass:
            status = "PASS ✓"
            total_pass += 1
        elif passed:
            status = "PARTIAL ◐"
            total_pass += 1
        else:
            status = "FAIL ✗"
            total_fail += 1

        print(f"\n       Result: {status}")
        if detected:
            print(f"       Detected: {detected}")
        if missed:
            print(f"       Missed:   {missed}")

        results[filename] = {
            "status": status,
            "findings_count": len(findings),
            "detected": detected,
            "missed": missed,
            "authenticity_score": job.authenticity_score,
        }

    db.close()

    # Summary
    print(f"\n{'=' * 70}")
    print(f"EVALUATION SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Total tests: {len(results)}")
    print(f"  Passed:      {total_pass}")
    print(f"  Failed:      {total_fail}")
    print(f"{'=' * 70}")

    for name, res in results.items():
        print(f"  {res['status']:12s} | {name}")
        print(f"              | Score: {res['authenticity_score']}, Findings: {res['findings_count']}")

    return total_fail == 0


if __name__ == "__main__":
    success = run_evaluation()
    sys.exit(0 if success else 1)
