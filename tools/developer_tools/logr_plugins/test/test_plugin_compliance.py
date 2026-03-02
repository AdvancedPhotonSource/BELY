"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.

Compliance tests that validate all bundled plugins have the required
structure. Parametrized over every plugin directory in plugins/.
"""

import os
import pytest

# Recognized xhtml subdirectories that plugins may use
RECOGNIZED_XHTML_SUBDIRS = {
    "about",
    "item",
    "itemDetailsViewSections",
    "propertyValue",
    "itemMultiEdit",
    "support",
}


def _plugin_path(plugins_dir, name):
    return os.path.join(plugins_dir, name)


@pytest.fixture(params=None)
def plugin_name(request):
    return request.param


def get_plugin_names(plugins_dir):
    from .conftest import EXCLUDED_PLUGINS

    return sorted(
        d
        for d in os.listdir(plugins_dir)
        if os.path.isdir(os.path.join(plugins_dir, d))
        and d not in EXCLUDED_PLUGINS
    )


@pytest.fixture
def all_plugin_paths(plugins_dir, plugin_names):
    """Return list of (name, path) tuples for all plugins."""
    return [(name, _plugin_path(plugins_dir, name)) for name in plugin_names]


class TestPluginCompliance:
    """Tests that all bundled plugins are structurally compliant."""

    @pytest.fixture(autouse=True)
    def _setup(self, plugins_dir, plugin_names):
        self.plugins_dir = plugins_dir
        self.plugin_names = plugin_names

    @pytest.mark.parametrize("plugin_name", get_plugin_names(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugins")
    ))
    def test_plugin_has_at_least_one_component(self, plugin_name):
        """Each plugin must have at least one of java/, xhtml/."""
        plugin_path = _plugin_path(self.plugins_dir, plugin_name)
        has_java = os.path.isdir(os.path.join(plugin_path, "java"))
        has_xhtml = os.path.isdir(os.path.join(plugin_path, "xhtml"))
        assert has_java or has_xhtml, (
            f"Plugin '{plugin_name}' has no java/ or xhtml/ directory"
        )

    @pytest.mark.parametrize("plugin_name", get_plugin_names(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugins")
    ))
    def test_java_plugin_has_plugin_manager(self, plugin_name):
        """If java/ exists, at least one *PluginManager.java file must be present."""
        java_dir = os.path.join(self.plugins_dir, plugin_name, "java")
        if not os.path.isdir(java_dir):
            pytest.skip(f"Plugin '{plugin_name}' has no java/ directory")

        manager_files = [
            f for f in os.listdir(java_dir)
            if f.endswith("PluginManager.java")
        ]
        assert len(manager_files) > 0, (
            f"Plugin '{plugin_name}' java/ has no *PluginManager.java file"
        )

    @pytest.mark.parametrize("plugin_name", get_plugin_names(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugins")
    ))
    def test_java_plugin_has_properties_file(self, plugin_name):
        """If java/ exists, a .properties config file must be present."""
        java_dir = os.path.join(self.plugins_dir, plugin_name, "java")
        if not os.path.isdir(java_dir):
            pytest.skip(f"Plugin '{plugin_name}' has no java/ directory")

        properties_files = [
            f for f in os.listdir(java_dir)
            if f.endswith(".properties")
        ]
        assert len(properties_files) > 0, (
            f"Plugin '{plugin_name}' java/ has no .properties config file"
        )

    @pytest.mark.parametrize("plugin_name", get_plugin_names(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugins")
    ))
    def test_xhtml_plugin_paths_valid(self, plugin_name):
        """If xhtml/ exists, all subdirectories must be recognized plugin paths."""
        xhtml_dir = os.path.join(self.plugins_dir, plugin_name, "xhtml")
        if not os.path.isdir(xhtml_dir):
            pytest.skip(f"Plugin '{plugin_name}' has no xhtml/ directory")

        subdirs = [
            d for d in os.listdir(xhtml_dir)
            if os.path.isdir(os.path.join(xhtml_dir, d))
        ]
        unrecognized = set(subdirs) - RECOGNIZED_XHTML_SUBDIRS
        assert len(unrecognized) == 0, (
            f"Plugin '{plugin_name}' xhtml/ has unrecognized subdirectories: {unrecognized}"
        )
