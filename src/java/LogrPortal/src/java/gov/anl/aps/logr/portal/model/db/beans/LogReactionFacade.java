/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.beans;

import gov.anl.aps.logr.portal.model.db.entities.LogReaction;
import gov.anl.aps.logr.portal.utilities.SessionUtility;
import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;

/**
 * Log reaction facade facilitates communication to db for the log reaction table. 
 * 
 * @author djarosz
 */
@Stateless
public class LogReactionFacade extends CdbEntityFacade<LogReaction> {

    @PersistenceContext(unitName = "LogrPortalPU")
    private EntityManager em;

    @Override
    protected EntityManager getEntityManager() {
        return em;
    }

    public LogReactionFacade() {
        super(LogReaction.class);
    }
    
    public static LogReactionFacade getInstance() {
        return (LogReactionFacade) SessionUtility.findFacade(LogReactionFacade.class.getSimpleName()); 
    }

}
