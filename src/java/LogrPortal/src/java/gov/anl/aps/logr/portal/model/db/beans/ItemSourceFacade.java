/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.beans;

import gov.anl.aps.logr.portal.model.db.entities.ItemSource;
import gov.anl.aps.logr.portal.utilities.SessionUtility;
import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;

/**
 *
 * @author djarosz
 */
@Stateless
public class ItemSourceFacade extends CdbEntityFacade<ItemSource> {

    @PersistenceContext(unitName = "LogrPortalPU")
    private EntityManager em;

    @Override
    protected EntityManager getEntityManager() {
        return em;
    }

    public ItemSourceFacade() {
        super(ItemSource.class);
    }
    
    public static ItemSourceFacade getInstance() {
        return (ItemSourceFacade) SessionUtility.findFacade(ItemSourceFacade.class.getSimpleName()); 
    }
    
}
