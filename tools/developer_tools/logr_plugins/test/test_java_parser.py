"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.

Tests for PluginJavaParser (utilities/plugin_java_parser.py).
"""

import os
from utilities.objects.cdb_plugin import CdbPlugin
from utilities.plugin_java_parser import PluginJavaParser


class TestGeneratePluginRegistrar:
    """Tests for generate_plugin_registrar_file_contents()."""

    def test_generate_plugin_registrar_empty(self, tmp_path):
        """With no plugins, generates registrar with empty markers."""
        config_storage = str(tmp_path / "config")
        os.makedirs(config_storage)
        parser = PluginJavaParser(config_storage)

        result = parser.generate_plugin_registrar_file_contents([])

        assert "class PluginRegistrar" in result
        assert "registerPlugins" in result
        assert "Recommended not to modify." in result
        # No import or register lines should be present
        assert "import gov.anl.aps.logr.portal.plugins.support." not in result.replace(
            "import gov.anl.aps.logr.portal.plugins.CdbPluginManager;", ""
        )

    def test_generate_plugin_registrar_with_plugins(self, tmp_path):
        """With deployed java plugin containing FooPluginManager.java,
        generates correct import and registration statements."""
        config_storage = str(tmp_path / "config")
        os.makedirs(config_storage)

        # Create mock deployed java plugin
        dist_dir = tmp_path / "dist"
        deploy_java_base = CdbPlugin.get_java_plugin_path(str(dist_dir))
        deploy_plugin_path = os.path.join(deploy_java_base, "testPlugin")
        os.makedirs(deploy_plugin_path)

        # Create a PluginManager file
        with open(os.path.join(deploy_plugin_path, "FooPluginManager.java"), "w") as f:
            f.write("// mock")

        # Create CdbPlugin and override deployed path
        plugin = CdbPlugin("testPlugin", str(tmp_path / "plugins"), str(dist_dir))

        parser = PluginJavaParser(config_storage)
        result = parser.generate_plugin_registrar_file_contents([plugin])

        assert "import gov.anl.aps.logr.portal.plugins.support.testPlugin.FooPluginManager;" in result
        assert "cdbPluginManager.registerPlugin(new FooPluginManager());" in result

    def test_plugin_manager_suffix_detection(self, tmp_path):
        """Only files ending in PluginManager.java are picked up."""
        config_storage = str(tmp_path / "config")
        os.makedirs(config_storage)

        dist_dir = tmp_path / "dist"
        deploy_java_base = CdbPlugin.get_java_plugin_path(str(dist_dir))
        deploy_plugin_path = os.path.join(deploy_java_base, "testPlugin")
        os.makedirs(deploy_plugin_path)

        # Create various files - only PluginManager ones should be picked up
        with open(os.path.join(deploy_plugin_path, "BarPluginManager.java"), "w") as f:
            f.write("// mock")
        with open(os.path.join(deploy_plugin_path, "SomeHelper.java"), "w") as f:
            f.write("// mock")
        with open(os.path.join(deploy_plugin_path, "SomeBean.java"), "w") as f:
            f.write("// mock")
        with open(os.path.join(deploy_plugin_path, "test.properties"), "w") as f:
            f.write("key=value")

        plugin = CdbPlugin("testPlugin", str(tmp_path / "plugins"), str(dist_dir))

        parser = PluginJavaParser(config_storage)
        result = parser.generate_plugin_registrar_file_contents([plugin])

        assert "BarPluginManager" in result
        assert "SomeHelper" not in result
        assert "SomeBean" not in result
