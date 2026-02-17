/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.beans;

import gov.anl.aps.logr.portal.model.db.entities.NotificationConfiguration;
import gov.anl.aps.logr.portal.model.db.entities.NotificationConfigurationHandlerSetting;
import gov.anl.aps.logr.portal.model.db.entities.NotificationHandlerConfigKey;
import gov.anl.aps.logr.portal.utilities.SessionUtility;
import java.util.List;
import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.NoResultException;
import javax.persistence.PersistenceContext;

/**
 * Facade for NotificationConfigurationHandlerSetting entity.
 * Provides database access methods for handler settings per notification configuration.
 *
 * @author djarosz
 */
@Stateless
public class NotificationConfigurationHandlerSettingFacade extends CdbEntityFacade<NotificationConfigurationHandlerSetting> {

    @PersistenceContext(unitName = "LogrPortalPU")
    private EntityManager em;

    @Override
    protected EntityManager getEntityManager() {
        return em;
    }

    public NotificationConfigurationHandlerSettingFacade() {
        super(NotificationConfigurationHandlerSetting.class);
    }

    public static NotificationConfigurationHandlerSettingFacade getInstance() {
        return (NotificationConfigurationHandlerSettingFacade) SessionUtility.findFacade(NotificationConfigurationHandlerSettingFacade.class.getSimpleName());
    }

    /**
     * Find all handler settings for a specific notification configuration.
     *
     * @param notificationConfiguration The notification configuration
     * @return List of handler settings for the configuration
     */
    public List<NotificationConfigurationHandlerSetting> findByNotificationConfiguration(NotificationConfiguration notificationConfiguration) {
        return em.createQuery(
                "SELECT n FROM NotificationConfigurationHandlerSetting n WHERE n.notificationConfiguration = :notificationConfiguration",
                NotificationConfigurationHandlerSetting.class)
                .setParameter("notificationConfiguration", notificationConfiguration)
                .getResultList();
    }

    /**
     * Find a specific handler setting for a configuration and key.
     *
     * @param notificationConfiguration The notification configuration
     * @param notificationHandlerConfigKey The handler config key
     * @return The matching setting or null if not found
     */
    public NotificationConfigurationHandlerSetting findByNotificationConfigurationAndKey(
            NotificationConfiguration notificationConfiguration,
            NotificationHandlerConfigKey notificationHandlerConfigKey) {
        try {
            return em.createQuery(
                    "SELECT n FROM NotificationConfigurationHandlerSetting n WHERE n.notificationConfiguration = :notificationConfiguration AND n.notificationHandlerConfigKeyId = :notificationHandlerConfigKey",
                    NotificationConfigurationHandlerSetting.class)
                    .setParameter("notificationConfiguration", notificationConfiguration)
                    .setParameter("notificationHandlerConfigKey", notificationHandlerConfigKey)
                    .getSingleResult();
        } catch (NoResultException ex) {
            return null;
        }
    }
}
