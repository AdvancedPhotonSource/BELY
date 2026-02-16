/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.beans;

import gov.anl.aps.logr.portal.model.db.entities.NotificationProvider;
import gov.anl.aps.logr.portal.model.db.entities.NotificationProviderConfigKey;
import gov.anl.aps.logr.portal.utilities.SessionUtility;
import java.util.List;
import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.NoResultException;
import javax.persistence.PersistenceContext;

/**
 * Facade for NotificationProviderConfigKey entity.
 * Provides database access methods for provider configuration keys.
 *
 * @author djarosz
 */
@Stateless
public class NotificationProviderConfigKeyFacade extends CdbEntityFacade<NotificationProviderConfigKey> {

    @PersistenceContext(unitName = "LogrPortalPU")
    private EntityManager em;

    @Override
    protected EntityManager getEntityManager() {
        return em;
    }

    public NotificationProviderConfigKeyFacade() {
        super(NotificationProviderConfigKey.class);
    }

    public static NotificationProviderConfigKeyFacade getInstance() {
        return (NotificationProviderConfigKeyFacade) SessionUtility.findFacade(NotificationProviderConfigKeyFacade.class.getSimpleName());
    }

    /**
     * Find all configuration keys for a specific provider ordered by display order.
     *
     * @param provider The notification provider
     * @return List of configuration keys for the provider
     */
    public List<NotificationProviderConfigKey> findByProvider(NotificationProvider provider) {
        return em.createQuery(
                "SELECT n FROM NotificationProviderConfigKey n WHERE n.notificationProviderId = :provider ORDER BY n.displayOrder",
                NotificationProviderConfigKey.class)
                .setParameter("provider", provider)
                .getResultList();
    }

    /**
     * Find a specific configuration key by provider and key name.
     *
     * @param provider The notification provider
     * @param configKey The configuration key name
     * @return The matching config key or null if not found
     */
    public NotificationProviderConfigKey findByProviderAndKey(NotificationProvider provider, String configKey) {
        try {
            return em.createQuery(
                    "SELECT n FROM NotificationProviderConfigKey n WHERE n.notificationProviderId = :provider AND n.configKey = :configKey",
                    NotificationProviderConfigKey.class)
                    .setParameter("provider", provider)
                    .setParameter("configKey", configKey)
                    .getSingleResult();
        } catch (NoResultException ex) {
            return null;
        }
    }
}
