/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.beans;

import gov.anl.aps.logr.portal.model.db.entities.UserSession;
import gov.anl.aps.logr.portal.utilities.SessionUtility;
import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.NoResultException;
import javax.persistence.PersistenceContext;

/**
 *
 * @author djarosz
 */
@Stateless
public class UserSessionFacade extends CdbEntityFacade<UserSession> {

    @PersistenceContext(unitName = "LogrPortalPU")
    private EntityManager em;

    @Override
    protected EntityManager getEntityManager() {
        return em;
    }

    public UserSessionFacade() {
        super(UserSession.class);
    }

    
    public UserSession findBySessionKey(String sessionKey) {
        try {
            return (UserSession) em.createNamedQuery("UserSession.findBySessionKey")
                    .setParameter("sessionKey", sessionKey)
                    .getSingleResult();
        } catch (NoResultException ex) {
        }
        return null;
    }    
    
    public static UserSessionFacade getInstance() {
        return (UserSessionFacade) SessionUtility.findFacade(UserSessionFacade.class.getSimpleName()); 
    }
    
}
