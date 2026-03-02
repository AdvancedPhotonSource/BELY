"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.

Tests for PluginXhtmlParser (utilities/plugin_xhtml_parser.py).
"""

import os
from utilities.objects.cdb_plugin import CdbPlugin
from utilities.plugin_xhtml_parser import (
    PluginXhtmlParser,
    ABOUT_PAGE_PLUGIN_DIALOGS_XHTML_FILENAME,
    ABOUT_PAGE_PLUGIN_LINKS_XHTML_FILENAME,
    UI_INCLUDE_SYNTAX,
)


class TestGenerateUiInclude:
    """Tests for the generate_ui_inlcude() method."""

    def test_generate_ui_include_existing_file(self, tmp_path):
        """Returns <ui:include> syntax when the file exists."""
        xhtml_base = tmp_path / "xhtml_plugins"
        plugin_xhtml = xhtml_base / "testPlugin" / "about"
        os.makedirs(plugin_xhtml)
        with open(plugin_xhtml / "dialogs.xhtml", "w") as f:
            f.write("<ui:composition/>")

        parser = PluginXhtmlParser(str(xhtml_base))
        result = parser.generate_ui_inlcude("about/dialogs.xhtml", "testPlugin")

        expected = UI_INCLUDE_SYNTAX % "testPlugin/about/dialogs.xhtml"
        assert result == expected
        assert "<ui:include" in result

    def test_generate_ui_include_missing_file(self, tmp_path):
        """Returns empty string when the file doesn't exist."""
        xhtml_base = tmp_path / "xhtml_plugins"
        os.makedirs(xhtml_base)

        parser = PluginXhtmlParser(str(xhtml_base))
        result = parser.generate_ui_inlcude("about/dialogs.xhtml", "nonexistent")

        assert result == ""


class TestGenerateXhtmlFilesContents:
    """Tests for generate_xhtml_files_contents()."""

    def test_generate_xhtml_files_contents(self, tmp_path):
        """With mock plugin xhtml structure, generates correct aggregated
        output with <ui:include> entries."""
        # Set up a mock deployed xhtml plugin path
        dist_dir = tmp_path / "dist"
        xhtml_base = CdbPlugin.get_xhtml_plugin_path(str(dist_dir))

        # Create plugin with about/ dialogs and links
        plugin_xhtml = os.path.join(xhtml_base, "mockPlugin", "about")
        os.makedirs(plugin_xhtml)
        with open(os.path.join(plugin_xhtml, "dialogs.xhtml"), "w") as f:
            f.write("<ui:composition/>")
        with open(os.path.join(plugin_xhtml, "links.xhtml"), "w") as f:
            f.write("<ui:composition/>")

        # Create CdbPlugin instance
        plugin = CdbPlugin("mockPlugin", str(tmp_path / "plugins"), str(dist_dir))

        parser = PluginXhtmlParser(xhtml_base)
        result = parser.generate_xhtml_files_contents([plugin])

        # Should produce a dict of xhtml filename -> content
        assert isinstance(result, dict)
        assert ABOUT_PAGE_PLUGIN_DIALOGS_XHTML_FILENAME in result
        assert ABOUT_PAGE_PLUGIN_LINKS_XHTML_FILENAME in result

        # The about dialogs file should contain the ui:include for our plugin
        dialogs_content = result[ABOUT_PAGE_PLUGIN_DIALOGS_XHTML_FILENAME]
        assert "mockPlugin/about/dialogs.xhtml" in dialogs_content
        assert "<ui:include" in dialogs_content
        assert "<ui:composition" in dialogs_content

        # The about links file should contain the ui:include for our plugin
        links_content = result[ABOUT_PAGE_PLUGIN_LINKS_XHTML_FILENAME]
        assert "mockPlugin/about/links.xhtml" in links_content

    def test_generate_xhtml_files_no_plugins(self, tmp_path):
        """With no plugins, generates template files with no ui:include entries."""
        xhtml_base = str(tmp_path / "xhtml_plugins")
        os.makedirs(xhtml_base)

        parser = PluginXhtmlParser(xhtml_base)
        result = parser.generate_xhtml_files_contents([])

        assert isinstance(result, dict)
        assert len(result) > 0
        # All values should be the template with no includes
        for filename, content in result.items():
            assert "<ui:composition" in content
            assert "<ui:include" not in content
