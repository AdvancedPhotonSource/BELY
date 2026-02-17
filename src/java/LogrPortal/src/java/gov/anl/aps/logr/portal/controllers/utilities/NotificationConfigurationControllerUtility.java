/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.utilities;

import gov.anl.aps.logr.common.exceptions.CdbException;
import gov.anl.aps.logr.common.exceptions.InvalidObjectState;
import gov.anl.aps.logr.portal.model.db.beans.NotificationConfigurationFacade;
import gov.anl.aps.logr.portal.model.db.beans.NotificationHandlerConfigKeyFacade;
import gov.anl.aps.logr.portal.model.db.entities.NotificationConfiguration;
import gov.anl.aps.logr.portal.model.db.entities.NotificationConfigurationHandlerSetting;
import gov.anl.aps.logr.portal.model.db.entities.NotificationConfigurationSetting;
import gov.anl.aps.logr.portal.model.db.entities.NotificationHandlerConfigKey;
import gov.anl.aps.logr.portal.model.db.entities.NotificationProvider;
import gov.anl.aps.logr.portal.model.db.entities.NotificationProviderConfigKey;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 *
 * @author djarosz
 */
public class NotificationConfigurationControllerUtility extends CdbEntityControllerUtility<NotificationConfiguration, NotificationConfigurationFacade> {

    @Override
    protected NotificationConfigurationFacade getEntityDbFacade() {
        return NotificationConfigurationFacade.getInstance();
    }

    @Override
    public NotificationConfiguration createEntityInstance(UserInfo sessionUser) {
        return new NotificationConfiguration();
    }

    @Override
    public String getEntityTypeName() {
        return "Notification Configuration";
    }

    @Override
    protected void prepareEntityInsert(NotificationConfiguration entity, UserInfo userInfo) throws CdbException {
        super.prepareEntityInsert(entity, userInfo);
        prepareEntityUpdateInsert(entity, userInfo);
    }

    @Override
    protected void prepareEntityUpdate(NotificationConfiguration entity, UserInfo updatedByUser) throws CdbException {
        super.prepareEntityUpdate(entity, updatedByUser);
        prepareEntityUpdateInsert(entity, updatedByUser);
    }

    private void prepareEntityUpdateInsert(NotificationConfiguration selected, UserInfo updatedByUser) throws InvalidObjectState {
        // Validate required fields
        if (selected.getName() == null || selected.getName().trim().isEmpty()) {
            throw new InvalidObjectState("Name is required");
        }
        NotificationProvider notificationProvider = selected.getNotificationProvider();

        if (notificationProvider == null) {
            throw new InvalidObjectState("Notification Provider is required");
        }
        if (selected.getNotificationEndpoint() == null || selected.getNotificationEndpoint().trim().isEmpty()) {
            throw new InvalidObjectState("Notification Endpoint is required");
        }

        // Validate required provider config keys
        List<NotificationProviderConfigKey> providerConfigKeys = selected.getProviderConfigKeys();
        Map<Integer, String> configSettings = selected.getConfigSettings();
        for (NotificationProviderConfigKey key : providerConfigKeys) {
            if (key.getIsRequired()) {
                String value = configSettings.get(key.getId());
                if (value == null || value.trim().isEmpty()) {
                    throw new InvalidObjectState(key.getDescription() + " is required");
                }
            }
        }
        UserInfo userInfo = selected.getUserInfo();
        if (userInfo == null) {
            throw new InvalidObjectState("User is required.");
        }

        // Populate notification provider config settings into entity format
        // Build map of existing settings by provider config key ID for reuse
        Map<Integer, NotificationConfigurationSetting> existingSettingsByKeyId = new HashMap<>();
        if (selected.getNotificationConfigurationSettingCollection() != null) {
            for (NotificationConfigurationSetting existing : selected.getNotificationConfigurationSettingCollection()) {
                existingSettingsByKeyId.put(existing.getNotificationProviderConfigKey().getId(), existing);
            }
        }

        List<NotificationConfigurationSetting> configSettingEntities = new ArrayList<>();
        for (NotificationProviderConfigKey key : providerConfigKeys) {
            String value = configSettings.get(key.getId());
            if (value != null && !value.trim().isEmpty()) {
                NotificationConfigurationSetting setting = existingSettingsByKeyId.get(key.getId());
                if (setting == null) {
                    setting = new NotificationConfigurationSetting();
                    setting.setNotificationConfiguration(selected);
                    setting.setNotificationProviderConfigKey(key);
                }
                setting.setConfigValue(value);
                configSettingEntities.add(setting);
            }
        }
        selected.setNotificationConfigurationSettingCollection(configSettingEntities);

        // Populate handler preferences into entity format
        // Build map of existing handler settings by handler config key ID for reuse
        Map<Integer, NotificationConfigurationHandlerSetting> existingHandlersByKeyId = new HashMap<>();
        if (selected.getNotificationConfigurationHandlerSettingCollection() != null) {
            for (NotificationConfigurationHandlerSetting existing : selected.getNotificationConfigurationHandlerSettingCollection()) {
                existingHandlersByKeyId.put(existing.getNotificationHandlerConfigKey().getId(), existing);
            }
        }

        List<NotificationConfigurationHandlerSetting> handlerSettingEntities = new ArrayList<>();
        Map<Integer, Boolean> handlerPreferences = selected.getHandlerPreferences();
        NotificationHandlerConfigKeyFacade handlerConfigKeyFacade = NotificationHandlerConfigKeyFacade.getInstance();
        for (Map.Entry<Integer, Boolean> entry : handlerPreferences.entrySet()) {
            if (entry.getValue() != null) {
                NotificationConfigurationHandlerSetting handlerSetting = existingHandlersByKeyId.get(entry.getKey());
                if (handlerSetting == null) {
                    NotificationHandlerConfigKey handlerKey = handlerConfigKeyFacade.find(entry.getKey());
                    if (handlerKey == null) {
                        continue;
                    }
                    handlerSetting = new NotificationConfigurationHandlerSetting();
                    handlerSetting.setNotificationConfiguration(selected);
                    handlerSetting.setNotificationHandlerConfigKey(handlerKey);
                }
                handlerSetting.setConfigValue(String.valueOf(entry.getValue()));
                handlerSettingEntities.add(handlerSetting);
            }
        }
        selected.setNotificationConfigurationHandlerSettingCollection(handlerSettingEntities);
    }

}
