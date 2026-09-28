"""Verification script to check SAGE-Indic foundation environment and imports."""

import sys


def main() -> int:
    print("=" * 60)
    print("SAGE-Indic Environment & Setup Verification")
    print("=" * 60)

    # 1. Python version
    print(f"Python version: {sys.version}")

    # 2. Package Import
    try:
        import sage_indic
        from sage_indic.config import get_settings
        from sage_indic.logging import get_logger, setup_logging

        print(f"Successfully imported sage_indic v{sage_indic.__version__}")
    except ImportError as e:
        print(f"ERROR importing sage_indic: {e}")
        return 1

    # 3. Settings & Directories
    setup_logging(level="INFO")
    logger = get_logger("verify_setup")
    logger.info("Testing logger configuration...")

    settings = get_settings()
    logger.info("Project Root: %s", settings.project_root)

    required_dirs = [
        settings.project_root / "src" / "sage_indic",
        settings.project_root / "tests",
        settings.project_root / "experiments",
        settings.project_root / "notebooks",
        settings.project_root / "data",
        settings.project_root / "configs",
        settings.project_root / "scripts",
        settings.project_root / "docs",
    ]

    all_ok = True
    for d in required_dirs:
        rel_path = d.relative_to(settings.project_root)
        if d.is_dir():
            print(f"  [OK] Directory exists: {rel_path}")
        else:
            print(f"  [FAIL] Directory missing: {rel_path}")
            all_ok = False

    if all_ok:
        print("\nAll foundation checks passed successfully!")
        return 0

    print("\nSome directory checks failed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
