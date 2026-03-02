/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.beans;

import gov.anl.aps.logr.portal.model.db.entities.NotificationHandlerConfigKey;
import gov.anl.aps.logr.portal.utilities.SessionUtility;
import java.util.List;
import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.NoResultException;
import javax.persistence.PersistenceContext;

/**
 * Facade for NotificationHandlerConfigKey entity.
 * Provides database access methods for handler configuration keys.
 *
 * @author djarosz
 */
@Stateless
public class NotificationHandlerConfigKeyFacade extends CdbEntityFacade<NotificationHandlerConfigKey> {

    @PersistenceContext(unitName = "LogrPortalPU")
    private EntityManager em;

    @Override
    protected EntityManager getEntityManager() {
        return em;
    }

    public NotificationHandlerConfigKeyFacade() {
        super(NotificationHandlerConfigKey.class);
    }

    public static NotificationHandlerConfigKeyFacade getInstance() {
        return (NotificationHandlerConfigKeyFacade) SessionUtility.findFacade(NotificationHandlerConfigKeyFacade.class.getSimpleName());
    }

    /**
     * Find all handler config keys ordered by display_order.
     *
     * @return List of all NotificationHandlerConfigKey entities
     */
    @Override
    public List<NotificationHandlerConfigKey> findAll() {
        return em.createNamedQuery("NotificationHandlerConfigKey.findAll", NotificationHandlerConfigKey.class)
                .getResultList();
    }

    /**
     * Find a specific handler config key by its config_key name.
     *
     * @param configKey The config key name (e.g., "entry_updates")
     * @return The matching NotificationHandlerConfigKey or null if not found
     */
    public NotificationHandlerConfigKey findByConfigKey(String configKey) {
        try {
            return em.createNamedQuery("NotificationHandlerConfigKey.findByConfigKey", NotificationHandlerConfigKey.class)
                    .setParameter("configKey", configKey)
                    .getSingleResult();
        } catch (NoResultException ex) {
            return null;
        }
    }
}
