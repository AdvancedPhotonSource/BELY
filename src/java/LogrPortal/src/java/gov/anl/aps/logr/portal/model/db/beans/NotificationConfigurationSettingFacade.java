/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.beans;

import gov.anl.aps.logr.portal.model.db.entities.NotificationConfiguration;
import gov.anl.aps.logr.portal.model.db.entities.NotificationConfigurationSetting;
import gov.anl.aps.logr.portal.model.db.entities.NotificationProviderConfigKey;
import gov.anl.aps.logr.portal.utilities.SessionUtility;
import java.util.List;
import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.NoResultException;
import javax.persistence.PersistenceContext;

/**
 * Facade for NotificationConfigurationSetting entity.
 * Provides database access methods for configuration settings.
 *
 * @author djarosz
 */
@Stateless
public class NotificationConfigurationSettingFacade extends CdbEntityFacade<NotificationConfigurationSetting> {

    @PersistenceContext(unitName = "LogrPortalPU")
    private EntityManager em;

    @Override
    protected EntityManager getEntityManager() {
        return em;
    }

    public NotificationConfigurationSettingFacade() {
        super(NotificationConfigurationSetting.class);
    }

    public static NotificationConfigurationSettingFacade getInstance() {
        return (NotificationConfigurationSettingFacade) SessionUtility.findFacade(NotificationConfigurationSettingFacade.class.getSimpleName());
    }

    /**
     * Find all settings for a specific notification configuration.
     *
     * @param notificationConfiguration The notification configuration
     * @return List of settings for the configuration
     */
    public List<NotificationConfigurationSetting> findByNotificationConfiguration(NotificationConfiguration notificationConfiguration) {
        return em.createQuery(
                "SELECT n FROM NotificationConfigurationSetting n WHERE n.notificationConfigurationId = :notificationConfiguration",
                NotificationConfigurationSetting.class)
                .setParameter("notificationConfiguration", notificationConfiguration)
                .getResultList();
    }

    /**
     * Find a specific setting for a configuration and key.
     *
     * @param notificationConfiguration The notification configuration
     * @param notificationProviderConfigKey The provider config key
     * @return The matching setting or null if not found
     */
    public NotificationConfigurationSetting findByNotificationConfigurationAndKey(
            NotificationConfiguration notificationConfiguration,
            NotificationProviderConfigKey notificationProviderConfigKey) {
        try {
            return em.createQuery(
                    "SELECT n FROM NotificationConfigurationSetting n WHERE n.notificationConfigurationId = :notificationConfiguration AND n.notificationProviderConfigKeyId = :notificationProviderConfigKey",
                    NotificationConfigurationSetting.class)
                    .setParameter("notificationConfiguration", notificationConfiguration)
                    .setParameter("notificationProviderConfigKey", notificationProviderConfigKey)
                    .getSingleResult();
        } catch (NoResultException ex) {
            return null;
        }
    }
}
