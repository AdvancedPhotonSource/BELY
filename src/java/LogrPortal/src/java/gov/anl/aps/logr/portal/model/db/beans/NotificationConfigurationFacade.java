/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.beans;

import gov.anl.aps.logr.portal.model.db.entities.NotificationConfiguration;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
import gov.anl.aps.logr.portal.utilities.SessionUtility;
import java.util.List;
import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.NoResultException;
import javax.persistence.PersistenceContext;

/**
 * Facade for NotificationConfiguration entity.
 * Provides database access methods for notification configurations.
 *
 * @author djarosz
 */
@Stateless
public class NotificationConfigurationFacade extends CdbEntityFacade<NotificationConfiguration> {

    @PersistenceContext(unitName = "LogrPortalPU")
    private EntityManager em;

    @Override
    protected EntityManager getEntityManager() {
        return em;
    }

    public NotificationConfigurationFacade() {
        super(NotificationConfiguration.class);
    }

    public static NotificationConfigurationFacade getInstance() {
        return (NotificationConfigurationFacade) SessionUtility.findFacade(NotificationConfigurationFacade.class.getSimpleName());
    }

    /**
     * Find all notification configurations for a specific user.
     *
     * @param user The user
     * @return List of notification configurations for the user
     */
    public List<NotificationConfiguration> findByUser(UserInfo user) {
        return em.createQuery(
                "SELECT n FROM NotificationConfiguration n WHERE n.userInfo = :user ORDER BY n.name",
                NotificationConfiguration.class)
                .setParameter("user", user)
                .getResultList();
    }

    /**
     * Find a notification configuration by name for a specific user.
     *
     * @param user The user
     * @param name The configuration name
     * @return The matching configuration or null if not found
     */
    public NotificationConfiguration findByUserAndName(UserInfo user, String name) {
        try {
            return em.createQuery(
                    "SELECT n FROM NotificationConfiguration n WHERE n.userInfo = :user AND n.name = :name",
                    NotificationConfiguration.class)
                    .setParameter("user", user)
                    .setParameter("name", name)
                    .getSingleResult();
        } catch (NoResultException ex) {
            return null;
        }
    }
}
