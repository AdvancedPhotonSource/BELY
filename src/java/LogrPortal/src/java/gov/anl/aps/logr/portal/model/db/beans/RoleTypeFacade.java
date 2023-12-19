/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.beans;

import gov.anl.aps.logr.portal.model.db.entities.RoleType;
import gov.anl.aps.logr.portal.utilities.SessionUtility;
import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;

/**
 *
 * @author djarosz
 */
@Stateless
public class RoleTypeFacade extends CdbEntityFacade<RoleType> {

    @PersistenceContext(unitName = "LogrPortalPU")
    private EntityManager em;

    @Override
    protected EntityManager getEntityManager() {
        return em;
    }

    public RoleTypeFacade() {
        super(RoleType.class);
    }
    
    public static RoleTypeFacade getInstance() {
        return (RoleTypeFacade) SessionUtility.findFacade(RoleTypeFacade.class.getSimpleName()); 
    }
    
}
