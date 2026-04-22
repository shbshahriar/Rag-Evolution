from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_DIR = ROOT / "datasets" / "markdown_docs"
SAMPLE_DIR = ROOT / "datasets" / "sample_docs"
STRUCTURED_DIR = ROOT / "datasets" / "structured_data"


TOPIC_PREFIXES = [
    ("01", "artificial_intelligence_and_ml"),
    ("02", "business_strategy_and_market_analysis"),
    ("03", "climate_change_and_environment"),
    ("04", "customer_support_and_troubleshooting"),
    ("05", "cybersecurity_and_incident_response"),
    ("06", "education_and_training_materials"),
    ("07", "financial_reporting_and_analysis"),
    ("08", "healthcare_and_clinical_guidelines"),
    ("09", "human_health_and_nutrition"),
    ("10", "legal_and_compliance_handbook"),
    ("11", "software_engineering_api_documentation"),
    ("12", "space_exploration"),
    ("13", "world_history_and_civilizations"),
]

STRUCTURED_PREFIXES = [
    ("01", "llm_models_comparison"),
    ("03", "climate_data"),
    ("09", "nutrition_facts"),
    ("12", "space_missions"),
    ("13", "historical_events"),
]


def copy_if_exists(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def main() -> None:
    copied: list[str] = []

    for prefix, stem in TOPIC_PREFIXES:
        for folder in (MARKDOWN_DIR, SAMPLE_DIR):
            for ext in (".md", ".docx", ".pdf"):
                src = folder / f"{stem}{ext}"
                if src.exists():
                    dst = folder / f"{prefix}_{stem}{ext}"
                    if copy_if_exists(src, dst):
                        copied.append(f"{src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")

    manifest_src = SAMPLE_DIR / "manifest.md"
    manifest_dst = SAMPLE_DIR / "00_manifest.md"
    if copy_if_exists(manifest_src, manifest_dst):
        copied.append(f"{manifest_src.relative_to(ROOT)} -> {manifest_dst.relative_to(ROOT)}")

    for prefix, stem in STRUCTURED_PREFIXES:
        src = STRUCTURED_DIR / f"{stem}.csv"
        if src.exists():
            dst = STRUCTURED_DIR / f"{prefix}_{stem}.csv"
            if copy_if_exists(src, dst):
                copied.append(f"{src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")

    print("Created numbered copies:")
    for item in copied:
        print(item)


if __name__ == "__main__":
    main()
