/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.plugins.support.menuBarLinks;

import java.util.List;

public class MenuBarItemObject {

    private String icon;
    private String text;
    private String href;
    private List<MenuBarItemObject> children;

    public MenuBarItemObject() {
    }

    public String getIcon() {
        return icon;
    }

    public void setIcon(String icon) {
        this.icon = icon;
    }

    public String getText() {
        return text;
    }

    public void setText(String text) {
        this.text = text;
    }

    public String getHref() {
        return href;
    }

    public void setHref(String href) {
        this.href = href;
    }

    public List<MenuBarItemObject> getChildren() {
        return children;
    }

    public void setChildren(List<MenuBarItemObject> children) {
        this.children = children;
    }

    public boolean getHasChildren() {
        return children != null && !children.isEmpty();
    }

}
