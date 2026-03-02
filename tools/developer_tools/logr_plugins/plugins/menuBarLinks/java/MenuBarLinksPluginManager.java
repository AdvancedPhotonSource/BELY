/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.plugins.support.menuBarLinks;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.reflect.TypeToken;
import gov.anl.aps.logr.portal.plugins.PluginManagerBase;
import java.lang.reflect.Type;
import java.util.LinkedList;
import java.util.List;
import java.util.Properties;

public class MenuBarLinksPluginManager extends PluginManagerBase {

    private static final Properties MENU_BAR_LINKS_PROPERTIES = getDefaultPropertiesForPlugin("menuBarLinks");

    private static final String MENU_ITEMS_KEY = "menuItems";

    private static List<MenuBarItemObject> MENU_BAR_ITEMS;

    public String getMenuItemsJsonTextProperty() {
        return MENU_BAR_LINKS_PROPERTIES.getProperty(MENU_ITEMS_KEY, "");
    }

    private void loadMenuBarItems() {
        Type resultType = new TypeToken<LinkedList<MenuBarItemObject>>() {}.getType();
        String json = getMenuItemsJsonTextProperty();

        Gson gson = new GsonBuilder().create();
        MENU_BAR_ITEMS = gson.fromJson(json, resultType);
    }

    @Override
    public List<?> getMenuBarItems() {
        if (MENU_BAR_ITEMS == null) {
            loadMenuBarItems();
        }
        return MENU_BAR_ITEMS;
    }

}
