"""Test that sage_indic can be imported and exports expected attributes."""

import sage_indic


def test_package_version():
    """Verify package version is defined."""
    assert hasattr(sage_indic, "__version__")
    assert isinstance(sage_indic.__version__, str)
    assert len(sage_indic.__version__) > 0


def test_package_exports():
    """Verify expected core utilities are exported from top-level package."""
    assert hasattr(sage_indic, "get_logger")
    assert hasattr(sage_indic, "setup_logging")
    assert hasattr(sage_indic, "get_settings")
    assert hasattr(sage_indic, "Settings")
