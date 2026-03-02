"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

import os
import pytest

# Plugins that are excluded from compliance tests (deprecated)
EXCLUDED_PLUGINS = {"pdmLink"}

LOGR_PLUGINS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def plugins_dir():
    """Absolute path to logr_plugins/plugins/."""
    return os.path.join(LOGR_PLUGINS_DIR, "plugins")


@pytest.fixture
def plugin_templates_dir():
    """Absolute path to logr_plugins/pluginTemplates/."""
    return os.path.join(LOGR_PLUGINS_DIR, "pluginTemplates")


@pytest.fixture
def plugin_names(plugins_dir):
    """List of all non-excluded plugin directory names."""
    names = sorted(
        d
        for d in os.listdir(plugins_dir)
        if os.path.isdir(os.path.join(plugins_dir, d))
        and d not in EXCLUDED_PLUGINS
    )
    return names


@pytest.fixture
def tmp_deploy_dir(tmp_path):
    """Temporary directory simulating deployment paths for parser tests."""
    return tmp_path / "deploy"
