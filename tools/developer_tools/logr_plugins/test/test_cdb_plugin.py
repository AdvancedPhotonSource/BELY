"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.

Tests for the CdbPlugin class (utilities/objects/cdb_plugin.py).
"""

import os
from utilities.objects.cdb_plugin import (
    CdbPlugin,
    CDB_PORTAL_CODE_PATH,
    CDB_WEB_SERVICE_CODE_PATH,
)


class TestGenerateSavedPaths:
    """Tests for CdbPlugin.generate_saved_paths()."""

    def test_generate_saved_paths(self, tmp_path):
        """Verifies correct path structure: {dir}/{name}/{type}."""
        plugin_dir = str(tmp_path / "plugins")
        plugin = CdbPlugin("myPlugin", plugin_dir, str(tmp_path / "dist"))

        assert plugin.xhtml_path == f"{plugin_dir}/myPlugin/xhtml"
        assert plugin.java_path == f"{plugin_dir}/myPlugin/java"
        assert plugin.python_path == f"{plugin_dir}/myPlugin/python"


class TestGenerateDeployedPaths:
    """Tests for CdbPlugin.generate_deployed_paths()."""

    def test_generate_deployed_paths(self, tmp_path):
        """Verifies correct deployment path patterns."""
        dist_dir = str(tmp_path / "dist")
        plugin = CdbPlugin("myPlugin", str(tmp_path / "plugins"), dist_dir)

        expected_xhtml = f"{dist_dir}/{CDB_PORTAL_CODE_PATH}/web/views/plugins/private/myPlugin"
        expected_java = f"{dist_dir}/{CDB_PORTAL_CODE_PATH}/src/java/gov/anl/aps/logr/portal/plugins/support/myPlugin"
        expected_python = f"{dist_dir}/{CDB_WEB_SERVICE_CODE_PATH}/cdb_web_service/plugins/myPlugin"

        assert plugin.deploy_xhtml_path == expected_xhtml
        assert plugin.deploy_java_path == expected_java
        assert plugin.deploy_python_path == expected_python


class TestStaticPathMethods:
    """Tests for static path generation methods."""

    def test_get_xhtml_plugin_path(self):
        result = CdbPlugin.get_xhtml_plugin_path("/opt/dist")
        assert result == f"/opt/dist/{CDB_PORTAL_CODE_PATH}/web/views/plugins/private"

    def test_get_java_plugin_path(self):
        result = CdbPlugin.get_java_plugin_path("/opt/dist")
        assert result == f"/opt/dist/{CDB_PORTAL_CODE_PATH}/src/java/gov/anl/aps/logr/portal/plugins/support"

    def test_get_python_plugin_path(self):
        result = CdbPlugin.get_python_plugin_path("/opt/dist")
        assert result == f"/opt/dist/{CDB_WEB_SERVICE_CODE_PATH}/cdb_web_service/plugins"


class TestHasMethods:
    """Tests for has_xhtml(), has_java(), has_python() path checks."""

    def test_has_methods_with_nonexistent_paths(self, tmp_path):
        """has_xhtml() etc. return False for nonexistent paths."""
        plugin = CdbPlugin("missing", str(tmp_path / "nonexistent"), str(tmp_path / "dist"))
        assert plugin.has_xhtml() is False
        assert plugin.has_java() is False
        assert plugin.has_python() is False

    def test_has_methods_with_existing_paths(self, tmp_path):
        """has_xhtml() etc. return True when directories exist."""
        plugin_dir = tmp_path / "plugins"
        os.makedirs(plugin_dir / "myPlugin" / "xhtml")
        os.makedirs(plugin_dir / "myPlugin" / "java")
        os.makedirs(plugin_dir / "myPlugin" / "python")

        plugin = CdbPlugin("myPlugin", str(plugin_dir), str(tmp_path / "dist"))
        assert plugin.has_xhtml() is True
        assert plugin.has_java() is True
        assert plugin.has_python() is True

    def test_has_deployed_methods_with_nonexistent_paths(self, tmp_path):
        """has_deployed_xhtml() etc. return False for nonexistent paths."""
        plugin = CdbPlugin("missing", str(tmp_path / "plugins"), str(tmp_path / "dist"))
        assert plugin.has_deployed_xhtml() is False
        assert plugin.has_deployed_java() is False
        assert plugin.has_deployed_python() is False
