/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers;

import gov.anl.aps.logr.portal.controllers.settings.NotificationConfigurationSettings;
import gov.anl.aps.logr.portal.controllers.utilities.NotificationConfigurationControllerUtility;
import gov.anl.aps.logr.common.mqtt.model.TestNotificationEvent;
import gov.anl.aps.logr.portal.model.db.beans.NotificationConfigurationFacade;
import gov.anl.aps.logr.portal.model.db.beans.NotificationConfigurationHandlerSettingFacade;
import gov.anl.aps.logr.portal.model.db.beans.NotificationConfigurationSettingFacade;
import gov.anl.aps.logr.portal.model.db.beans.NotificationHandlerConfigKeyFacade;
import gov.anl.aps.logr.portal.model.db.beans.NotificationProviderConfigKeyFacade;
import gov.anl.aps.logr.portal.model.db.beans.NotificationProviderFacade;
import gov.anl.aps.logr.portal.model.db.entities.NotificationConfiguration;
import gov.anl.aps.logr.portal.model.db.entities.NotificationConfigurationHandlerSetting;
import gov.anl.aps.logr.portal.model.db.entities.NotificationConfigurationSetting;
import gov.anl.aps.logr.portal.model.db.entities.NotificationHandlerConfigKey;
import gov.anl.aps.logr.portal.model.db.entities.NotificationProvider;
import gov.anl.aps.logr.portal.model.db.entities.NotificationProviderConfigKey;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
import gov.anl.aps.logr.portal.utilities.SessionUtility;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import javax.ejb.EJB;
import javax.enterprise.context.SessionScoped;
import javax.faces.component.UIComponent;
import javax.faces.context.FacesContext;
import javax.faces.convert.Converter;
import javax.faces.convert.FacesConverter;
import javax.inject.Named;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

/**
 * Controller for managing notification configurations. Handles CRUD operations
 * for user notification configurations including provider settings and handler
 * preferences.
 *
 * @author djarosz
 */
@Named(NotificationConfigurationController.CONTROLLER_NAMED)
@SessionScoped
public class NotificationConfigurationController extends CdbEntityController<NotificationConfigurationControllerUtility, NotificationConfiguration, NotificationConfigurationFacade, NotificationConfigurationSettings> implements Serializable {

    public static final String CONTROLLER_NAMED = "notificationConfigurationController";

    public static final String APPRISE_NOTIFICATION_PROVIDER_NAME = "apprise";

    private static final Logger logger = LogManager.getLogger(NotificationConfigurationController.class.getName());

    @EJB
    private NotificationProviderFacade notificationProviderFacade;

    @EJB
    private NotificationHandlerConfigKeyFacade notificationHandlerConfigKeyFacade;

    @EJB
    private NotificationConfigurationHandlerSettingFacade notificationConfigurationHandlerSettingFacade;

    @EJB
    private NotificationProviderConfigKeyFacade notificationProviderConfigKeyFacade;

    @EJB
    private NotificationConfigurationSettingFacade notificationConfigurationSettingFacade;

    @EJB
    private NotificationConfigurationFacade notificationConfigurationFacade;

    @Override
    protected NotificationConfigurationControllerUtility createControllerUtilityInstance() {
        return new NotificationConfigurationControllerUtility();
    }

    @Override
    protected NotificationConfigurationSettings createNewSettingObject() {
        return new NotificationConfigurationSettings();
    }

    @Override
    protected NotificationConfigurationFacade getEntityDbFacade() {
        return notificationConfigurationFacade;
    }

    /**
     * Get all configurations for the current logged-in user.
     *
     * @return
     */
    public List<NotificationConfiguration> getItemsForCurrentUser() {
        UserInfoController instance = UserInfoController.getInstance();
        UserInfo currentUserInfoUser = instance.getCurrent();
        if (currentUserInfoUser != null) {
            return notificationConfigurationFacade.findByUser(currentUserInfoUser);
        }
        return new ArrayList<>();
    }

    /**
     * Get all available notification providers.
     *
     * @return
     */
    public List<NotificationProvider> getAvailableProviders() {
        return notificationProviderFacade.findAll();
    }

    /**
     * Called when provider is selected in dialog.
     */
    public void onProviderChange() {
        NotificationProvider provider = getCurrent().getNotificationProvider();
        if (provider != null) {
            loadProviderConfigKeys();
        } else {
            NotificationConfiguration current = getCurrent();
            current.getProviderConfigKeys().clear();
            current.getConfigSettings().clear();
        }
    }
//

    /**
     * Prepare to create a new configuration.
     *
     * @param userInfo
     */
    public void prepareCreateDialog(UserInfo userInfo) {
        super.prepareCreate();
        NotificationConfiguration current = getCurrent();
        current.setUserInfo(userInfo);

        // Load default handler preferences
        Map<Integer, Boolean> handlerPreferences = current.getHandlerPreferences();
        List<NotificationHandlerConfigKey> handlerKeys = notificationHandlerConfigKeyFacade.findAll();
        for (NotificationHandlerConfigKey key : handlerKeys) {
            handlerPreferences.put(key.getId(), "true".equalsIgnoreCase(key.getDefaultValue()));
        }
    }

    /**
     * Prepare to create a new email notification configuration with user's
     * email pre-filled.
     */
    public void populateEmailInfo() {
        NotificationConfiguration current = getCurrent();
        UserInfo currentUser = current.getUserInfo();

        // Find Apprise provider
        NotificationProvider appriseProvider = notificationProviderFacade.findByName(APPRISE_NOTIFICATION_PROVIDER_NAME);
        if (appriseProvider == null) {
            SessionUtility.addErrorMessage("Error", "Apprise provider not found in database");
            return;
        }

        // Set provider
        current.setNotificationProvider(appriseProvider);
        loadProviderConfigKeys();

        // Pre-fill name and notification endpoint with user's email
        current.setName(currentUser.getUsername() + " Email Notifications");
        current.setDescription("Email notifications for " + currentUser.getUsername());
        current.setNotificationEndpoint("mailto://" + currentUser.getEmail());
    }

    /**
     * Prepare to edit an existing configuration.
     */
    public void prepareEditDialog(NotificationConfiguration config) {
        super.prepareEdit(config);
        setCurrent(config);

        NotificationConfiguration current = getCurrent();

        Map<Integer, String> configSettings = current.getConfigSettings();

        configSettings.clear();

        // Load provider info
        NotificationProvider provider = config.getNotificationProvider();
        if (provider != null) {
            loadProviderConfigKeys();

            // Load existing config settings
            List<NotificationConfigurationSetting> existingSettings
                    = notificationConfigurationSettingFacade.findByNotificationConfiguration(config);
            for (NotificationConfigurationSetting setting : existingSettings) {
                configSettings.put(setting.getNotificationProviderConfigKey().getId(),
                        setting.getConfigValue());
            }

            // Load existing handler preferences
            populateHandlerPreferences(config);
        }
    }

    private void populateHandlerPreferences(NotificationConfiguration config) {
        Map<Integer, Boolean> handlerPreferences = config.getHandlerPreferences();
        handlerPreferences.clear();

        List<NotificationConfigurationHandlerSetting> handlerSettings
                = notificationConfigurationHandlerSettingFacade.findByNotificationConfiguration(config);
        for (NotificationConfigurationHandlerSetting setting : handlerSettings) {
            handlerPreferences.put(setting.getNotificationHandlerConfigKey().getId(),
                    "true".equalsIgnoreCase(setting.getConfigValue()));
        }
    }

    /**
     * Save the configuration (create or update).
     */
    public void save() {
        NotificationConfiguration current = getCurrent();

        if (current.getId() == null) {
            create();
        } else {
            update();
        }
    }

    private void loadProviderConfigKeys() {
        NotificationConfiguration current = getCurrent();

        NotificationProvider provider = getCurrent().getNotificationProvider();
        List<NotificationProviderConfigKey> providerConfigKeys = notificationProviderConfigKeyFacade.findByProvider(provider);
        current.setProviderConfigKeys(providerConfigKeys);
        Map<Integer, String> configSettings = current.getConfigSettings();

        for (NotificationProviderConfigKey key : providerConfigKeys) {
            if (!configSettings.containsKey(key.getId())) {
                configSettings.put(key.getId(), "");
            }
        }
    }

    /**
     * Get active handler preferences for a configuration (for display in
     * table).
     *
     * @param config
     * @return
     */
    public List<NotificationHandlerConfigKey> getActiveHandlerPreferences(NotificationConfiguration config) {
        List<NotificationHandlerConfigKey> active = new ArrayList<>();
        List<NotificationConfigurationHandlerSetting> settings
                = notificationConfigurationHandlerSettingFacade.findByNotificationConfiguration(config);

        for (NotificationConfigurationHandlerSetting setting : settings) {
            if ("true".equalsIgnoreCase(setting.getConfigValue())) {
                active.add(setting.getNotificationHandlerConfigKey());
            }
        }
        return active;
    }

    /**
     * Send a test notification via MQTT.
     *
     * @param config
     */
    public void sendTestNotification(NotificationConfiguration config) {
        try {
            // Get current username
            UserInfoController userInfoController = UserInfoController.getInstance();
            String username = userInfoController.getCurrent().getUsername();

            // Build provider settings map from persisted configuration settings
            Map<String, String> providerSettings = new HashMap<>();
            Collection<NotificationConfigurationSetting> settingsCollection
                    = config.getNotificationConfigurationSettingCollection();
            if (settingsCollection != null) {
                for (NotificationConfigurationSetting setting : settingsCollection) {
                    String key = setting.getNotificationProviderConfigKey().getConfigKey();
                    String value = setting.getConfigValue();
                    if (key != null && value != null && !value.isEmpty()) {
                        providerSettings.put(key, value);
                    }
                }
            }

            // Create test notification event
            TestNotificationEvent event = new TestNotificationEvent(
                    config.getNotificationEndpoint(),
                    config.getName(),
                    config.getId(),
                    providerSettings.isEmpty() ? null : providerSettings,
                    username
            );

            SessionUtility.publishMqttEvent(event);
            SessionUtility.addInfoMessage("Test Sent",
                    "Test notification sent to: " + config.getName());
        } catch (Exception ex) {
            SessionUtility.addErrorMessage("Error",
                    "Failed to send test notification: " + ex.getMessage());
            logger.error("Failed to send test notification", ex);
        }
    }

    /**
     * Process unsubscribe request from URL parameters. Called by f:viewAction
     * on page load.
     */
    public void processUnsubscribeRequest() {
        LoginController loginController = LoginController.getInstance();
        if (!loginController.isLoggedIn()) {
            return;
        }

        String configIdStr = SessionUtility.getRequestParameterValue("configId");
        String notificationType = SessionUtility.getRequestParameterValue("notificationType");

        if (configIdStr == null || notificationType == null) {
            SessionUtility.addErrorMessage("Error", "Invalid unsubscribe request. Missing required parameters.");
            return;
        }

        Integer configId;
        try {
            configId = Integer.valueOf(configIdStr);
        } catch (NumberFormatException ex) {
            SessionUtility.addErrorMessage("Error", "Invalid configuration ID.");
            return;
        }

        NotificationConfiguration config = findById(configId);
        setCurrent(config);
        populateHandlerPreferences(config);

        if (config == null) {
            SessionUtility.addErrorMessage("Error", "Notification configuration not found.");
            return;
        }

        // Verify ownership or admin
        UserInfo currentUser = SessionUtility.getUser();
        boolean isAdmin = loginController.isLoggedInAsAdmin();
        boolean isOwner = currentUser != null && config.getUserInfo() != null
                && currentUser.getId().equals(config.getUserInfo().getId());
        if (!isAdmin && !isOwner) {
            String ownerName = config.getUserInfo() != null ? config.getUserInfo().getUsername() : "unknown";
            config.setUnsubscribeError("This notification configuration belongs to " + ownerName
                    + ". You do not have permission to modify it.");
            return;
        }

        if (isAdmin && !isOwner) {
            config.setUnsubscribeForOtherUser(true);
        }

        // Find handler key
        NotificationHandlerConfigKey handlerKey = notificationHandlerConfigKeyFacade.findByConfigKey(notificationType);
        if (handlerKey == null) {
            config.setUnsubscribeError("Unknown notification type: " + notificationType);
            return;
        }

        config.setUnsubscribeHandlerConfigKey(handlerKey);

        // Check if already unsubscribed
        Boolean currentValue = getCurrent().getHandlerPreferences().get(handlerKey.getId());
        if (currentValue != null && !currentValue) {
            config.setAlreadyUnsubscribed(true);
        }
    }

    /**
     * Execute the unsubscribe action. Disables the notification type for the
     * current configuration using the standard update flow.
     */
    public void executeUnsubscribe() {
        NotificationConfiguration current = getCurrent();
        if (current == null) {
            current.setUnsubscribeError("No configuration selected.");
            return;
        }

        NotificationHandlerConfigKey handlerKey = current.getUnsubscribeHandlerConfigKey();
        if (handlerKey == null) {
            current.setUnsubscribeError("No notification type selected.");
            return;
        }

        try {
            current.getHandlerPreferences().put(handlerKey.getId(), false);
            update();

            boolean unsubscribeForOtherUser = current.isUnsubscribeForOtherUser();

            // Get updated current.
            current = getCurrent();
            current.setUnsubscribeComplete(true);
            current.setUnsubscribeForOtherUser(unsubscribeForOtherUser);
        } catch (Exception ex) {
            current.setUnsubscribeError("Failed to update notification setting: " + ex.getMessage());
            logger.error("Failed to execute unsubscribe", ex);
        }
    }

    /**
     * Cancel the unsubscribe action and return to user profile.
     *
     * @return Navigation outcome
     */
    public String cancelUnsubscribe() {
        return redirectToSettingsForCurrentConfigurationUser();
    }

    public String redirectToSettingsForCurrentConfigurationUser() {
        UserInfoController instance = UserInfoController.getInstance();

        NotificationConfiguration current = getCurrent();
        if (current != null) {
            instance.prepareView(current.getUserInfo());

            return "/views/userInfo/edit.xhtml?faces-redirect=true";
        }

        SessionUtility.addErrorMessage("Error", "No configuration");

        return "/";
    }

    public NotificationProvider getSelectedProvider() {
        return getCurrent().getNotificationProvider();
    }

    public NotificationProvider findProviderById(Integer id) {
        return notificationProviderFacade.find(id);
    }

    @Override
    public String destroy() {
        super.destroy();
        return null;
    }

    public static NotificationConfigurationController getInstance() {
        return (NotificationConfigurationController) SessionUtility.findBean(NotificationConfigurationController.CONTROLLER_NAMED);
    }

    public List<NotificationHandlerConfigKey> getAvailableHandlerConfigKeys() {
        return notificationHandlerConfigKeyFacade.findAll();
    }

    @FacesConverter(value = "notificationProviderConverter")
    public static class NotificationProviderConverter implements Converter {

        @Override
        public Object getAsObject(FacesContext facesContext, UIComponent component, String value) {
            if (value == null || value.length() == 0 || "null".equals(value)) {
                return null;
            }
            NotificationConfigurationController controller = (NotificationConfigurationController) facesContext.getApplication().getELResolver().
                    getValue(facesContext.getELContext(), null, NotificationConfigurationController.CONTROLLER_NAMED);
            return controller.findProviderById(getKey(value));
        }

        java.lang.Integer getKey(String value) {
            java.lang.Integer key;
            key = Integer.valueOf(value);
            return key;
        }

        String getStringKey(java.lang.Integer value) {
            StringBuilder sb = new StringBuilder();
            sb.append(value);
            return sb.toString();
        }

        @Override
        public String getAsString(FacesContext facesContext, UIComponent component, Object object) {
            if (object == null) {
                return "";
            }
            if (object instanceof NotificationProvider) {
                NotificationProvider o = (NotificationProvider) object;
                return getStringKey(o.getId());
            } else {
                throw new IllegalArgumentException("object " + object + " is of type " + object.getClass().getName() + "; expected type: " + NotificationProvider.class.getName());
            }
        }

    }
}
