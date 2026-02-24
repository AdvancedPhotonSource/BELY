/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.settings;

import javax.faces.event.ActionEvent;
import org.primefaces.component.datatable.DataTable;

/**
 *
 * @author djarosz
 */
public class NotificationConfigurationSettings implements ICdbSettings {

    @Override
    public boolean updateSettings() {
        return false;
    }

    @Override
    public void saveDisplayListPageHelpFragmentActionListener() {

    }

    @Override
    public void saveListSettingsForSessionSettingEntityActionListener(ActionEvent actionEvent) {

    }

    @Override
    public void updateListSettingsFromListDataTable(DataTable dataTable) {

    }

    @Override
    public void clearListFilters() {

    }

    @Override
    public void clearSelectFilters() {

    }

}
