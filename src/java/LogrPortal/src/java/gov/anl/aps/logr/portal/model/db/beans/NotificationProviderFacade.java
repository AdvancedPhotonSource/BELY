/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.beans;

import gov.anl.aps.logr.portal.model.db.entities.NotificationProvider;
import gov.anl.aps.logr.portal.utilities.SessionUtility;
import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.NoResultException;
import javax.persistence.PersistenceContext;

/**
 * Facade for NotificationProvider entity.
 * Provides database access methods for notification providers.
 *
 * @author djarosz
 */
@Stateless
public class NotificationProviderFacade extends CdbEntityFacade<NotificationProvider> {

    @PersistenceContext(unitName = "LogrPortalPU")
    private EntityManager em;

    @Override
    protected EntityManager getEntityManager() {
        return em;
    }

    public NotificationProviderFacade() {
        super(NotificationProvider.class);
    }

    public static NotificationProviderFacade getInstance() {
        return (NotificationProviderFacade) SessionUtility.findFacade(NotificationProviderFacade.class.getSimpleName());
    }

    /**
     * Find a notification provider by name.
     *
     * @param name The provider name
     * @return The matching provider or null if not found
     */
    public NotificationProvider findByName(String name) {
        try {
            return em.createNamedQuery("NotificationProvider.findByName", NotificationProvider.class)
                    .setParameter("name", name)
                    .getSingleResult();
        } catch (NoResultException ex) {
            return null;
        }
    }
}
