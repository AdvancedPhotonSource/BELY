/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.beans;

import gov.anl.aps.logr.portal.model.db.entities.EntityInfo;
import gov.anl.aps.logr.portal.utilities.SessionUtility;
import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;

/**
 *
 * @author djarosz
 */
@Stateless
public class EntityInfoFacade extends CdbEntityFacade<EntityInfo> {

    @PersistenceContext(unitName = "LogrPortalPU")
    private EntityManager em;

    @Override
    protected EntityManager getEntityManager() {
        return em;
    }

    public EntityInfoFacade() {
        super(EntityInfo.class);
    }
    
    public static EntityInfoFacade getInstance() {
        return (EntityInfoFacade) SessionUtility.findFacade(EntityInfoFacade.class.getSimpleName()); 
    }
    
}
