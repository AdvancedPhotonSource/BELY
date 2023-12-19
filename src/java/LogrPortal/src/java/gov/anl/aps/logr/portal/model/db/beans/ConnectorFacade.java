/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.beans;

import gov.anl.aps.logr.portal.model.db.entities.Connector;
import gov.anl.aps.logr.portal.utilities.SessionUtility;
import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;

/**
 *
 * @author djarosz
 */
@Stateless
public class ConnectorFacade extends CdbEntityFacade<Connector> {

    @PersistenceContext(unitName = "LogrPortalPU")
    private EntityManager em;

    @Override
    protected EntityManager getEntityManager() {
        return em;
    }

    public ConnectorFacade() {
        super(Connector.class);
    }
    
    public static ConnectorFacade getInstance() {
        return (ConnectorFacade) SessionUtility.findFacade(ConnectorFacade.class.getSimpleName()); 
    }

    
}
