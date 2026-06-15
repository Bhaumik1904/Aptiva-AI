"""
APTIVA AI — Dataset Loader
Handles ZIP auto-detection, extraction, file discovery, validation,
schema loading, and dataset statistics. No manual extraction required.
"""

import glob
import json
import os
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ── File discovery mapping ────────────────────────────────────────────────────

EXPECTED_FILES = {
    "candidates_jsonl": ["candidates.jsonl"],
    "sample_candidates": ["sample_candidates.json"],
    "candidate_schema": ["candidate_schema.json"],
    "job_description": ["job_description.docx"],
    "signals_doc": ["redrob_signals_doc.docx"],
    "submission_spec": ["submission_spec.docx"],
    "sample_submission": ["sample_submission.csv"],
    "validate_script": ["validate_submission.py"],
    "submission_metadata": ["submission_metadata_template.yaml", "submission_metadata.yaml"],
}


class DatasetLoader:
    """
    Manages the hackathon dataset lifecycle:
    1. Detect ZIP in data_dir
    2. Extract on first run
    3. Discover all expected files
    4. Validate presence and load schema
    5. Provide statistics
    """

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.discovered: Dict[str, Optional[Path]] = {}
        self.extraction_log: List[str] = []
        self._extracted = False

    # ── ZIP Detection & Extraction ────────────────────────────────────────────

    def auto_setup(self) -> Dict[str, Any]:
        """
        Full setup: detect ZIP → extract → discover files → return status.
        Returns a status dict describing what was found.
        """
        status = {
            "zip_found": False,
            "zip_path": None,
            "extracted": False,
            "files_found": {},
            "dataset_ready": False,
            "warnings": [],
        }

        # Step 1: Check if already extracted (skip re-extraction)
        self._discover_files()
        if self.discovered.get("candidates_jsonl") or self.discovered.get("sample_candidates"):
            status["extracted"] = True
            status["files_found"] = {k: str(v) for k, v in self.discovered.items() if v}
            status["dataset_ready"] = self._check_minimum_viable()
            return status

        # Step 2: Find ZIP file
        zip_path = self._find_zip()
        if not zip_path:
            status["warnings"].append(
                "No ZIP file found in data/ directory. "
                "Please place the hackathon dataset ZIP in d:\\Aptiva AI\\data\\"
            )
            return status

        status["zip_found"] = True
        status["zip_path"] = str(zip_path)

        # Step 3: Extract
        try:
            self._extract_zip(zip_path)
            status["extracted"] = True
            self._extracted = True
        except Exception as e:
            status["warnings"].append(f"ZIP extraction failed: {e}")
            return status

        # Step 4: Discover after extraction
        self._discover_files()
        status["files_found"] = {k: str(v) for k, v in self.discovered.items() if v}
        status["dataset_ready"] = self._check_minimum_viable()

        if not self.discovered.get("candidates_jsonl"):
            status["warnings"].append(
                "candidates.jsonl not found after extraction. "
                "Will use sample_candidates.json for demo mode."
            )

        return status

    def _find_zip(self) -> Optional[Path]:
        """Find any .zip file in the data directory."""
        zips = list(self.data_dir.glob("*.zip"))
        if zips:
            # Prefer the largest ZIP (likely the dataset)
            return max(zips, key=lambda p: p.stat().st_size)
        # Also check parent directory
        parent_zips = list(self.data_dir.parent.glob("*.zip"))
        if parent_zips:
            return max(parent_zips, key=lambda p: p.stat().st_size)
        return None

    def _extract_zip(self, zip_path: Path) -> None:
        """Extract ZIP to data directory, flattening nested directories."""
        with zipfile.ZipFile(zip_path, "r") as zf:
            members = zf.namelist()
            self.extraction_log = members
            for member in members:
                # Flatten: strip leading directory component
                parts = Path(member).parts
                if len(parts) > 1:
                    # File is in a subdirectory — extract to data_dir directly
                    filename = parts[-1]
                    if filename:  # Skip directory entries
                        target = self.data_dir / filename
                        if not target.exists():
                            source = zf.open(member)
                            target.write_bytes(source.read())
                else:
                    zf.extract(member, self.data_dir)

    # ── File Discovery ────────────────────────────────────────────────────────

    def _discover_files(self) -> None:
        """Recursively search data_dir for all expected files."""
        self.discovered = {}
        for key, filenames in EXPECTED_FILES.items():
            found = None
            for fname in filenames:
                # Direct match
                candidate = self.data_dir / fname
                if candidate.exists():
                    found = candidate
                    break
                # Recursive search
                matches = list(self.data_dir.rglob(fname))
                if matches:
                    found = matches[0]
                    break
            self.discovered[key] = found

    def _check_minimum_viable(self) -> bool:
        """Dataset is viable if we have at least candidates or sample."""
        return bool(
            self.discovered.get("candidates_jsonl")
            or self.discovered.get("sample_candidates")
        )

    # ── Data Loading ──────────────────────────────────────────────────────────

    def get_candidates_path(self) -> Optional[Path]:
        """Return path to main candidates file (full or sample)."""
        return (
            self.discovered.get("candidates_jsonl")
            or self.discovered.get("sample_candidates")
        )

    def get_sample_candidates_path(self) -> Optional[Path]:
        """Return path to sample_candidates.json specifically."""
        return self.discovered.get("sample_candidates")

    def load_schema(self) -> Optional[Dict]:
        """Load candidate_schema.json if available."""
        schema_path = self.discovered.get("candidate_schema")
        if schema_path and schema_path.exists():
            with open(schema_path, encoding="utf-8") as f:
                return json.load(f)
        return None

    def load_sample_candidates(self) -> List[Dict]:
        """Load sample_candidates.json as a list of dicts."""
        path = self.discovered.get("sample_candidates")
        if not path or not path.exists():
            return []
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        # May be a list or wrapped object
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "candidates" in data:
            return data["candidates"]
        return []

    def stream_candidates(self, path: Optional[Path] = None):
        """
        Generator: yield candidate dicts one at a time.
        Supports .jsonl and .json (array) formats.
        """
        target = path or self.get_candidates_path()
        if not target or not target.exists():
            return

        if target.suffix == ".json":
            # JSON array — load all at once
            candidates = self.load_sample_candidates()
            yield from candidates
            return

        # JSONL — stream line by line
        import gzip
        opener = gzip.open if str(target).endswith(".gz") else open
        mode = "rt"
        with opener(target, mode, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue

    def load_all_candidates(self, path: Optional[Path] = None) -> List[Dict]:
        """Load all candidates into memory. Use only when RAM allows."""
        return list(self.stream_candidates(path))

    # ── Statistics ────────────────────────────────────────────────────────────

    def get_dataset_stats(self, candidates: List[Dict]) -> Dict[str, Any]:
        """Compute basic statistics over a loaded candidate list."""
        if not candidates:
            return {}

        yoe_values = [c["profile"].get("years_of_experience", 0) for c in candidates]
        titles = [c["profile"].get("current_title", "Unknown") for c in candidates]
        countries = [c["profile"].get("country", "Unknown") for c in candidates]
        active_flags = [
            c["redrob_signals"].get("open_to_work_flag", False) for c in candidates
        ]
        notice_periods = [
            c["redrob_signals"].get("notice_period_days", 0) for c in candidates
        ]

        return {
            "total_candidates": len(candidates),
            "avg_experience": round(sum(yoe_values) / len(yoe_values), 1) if yoe_values else 0,
            "open_to_work": sum(1 for f in active_flags if f),
            "avg_notice_days": round(sum(notice_periods) / len(notice_periods), 1) if notice_periods else 0,
            "countries": len(set(countries)),
            "unique_titles": len(set(titles)),
        }

    def get_file_manifest(self) -> Dict[str, str]:
        """Return a human-readable manifest of discovered files."""
        return {
            key: str(path) if path else "NOT FOUND"
            for key, path in self.discovered.items()
        }
