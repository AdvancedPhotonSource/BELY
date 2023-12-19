/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.beans;

import gov.anl.aps.logr.portal.model.db.entities.PropertyTypeHandler;
import gov.anl.aps.logr.portal.utilities.SessionUtility;
import java.util.List;
import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.NoResultException;
import javax.persistence.PersistenceContext;

/**
 *
 * @author djarosz
 */
@Stateless
public class PropertyTypeHandlerFacade extends CdbEntityFacade<PropertyTypeHandler> {

    @PersistenceContext(unitName = "LogrPortalPU")
    private EntityManager em;

    @Override
    protected EntityManager getEntityManager() {
        return em;
    }

    public PropertyTypeHandlerFacade() {
        super(PropertyTypeHandler.class);
    }
    
    @Override
    public List<PropertyTypeHandler> findAll() {
        return (List<PropertyTypeHandler>) em.createNamedQuery("PropertyTypeHandler.findAll")
                .getResultList();
    }
    
     public PropertyTypeHandler findByName(String name) {
        try {
            return (PropertyTypeHandler) em.createNamedQuery("PropertyTypeHandler.findByName")
                    .setParameter("name", name)
                    .getSingleResult();
        } catch (NoResultException ex) {
        }
        return null;
    }
     
    public static PropertyTypeHandlerFacade getInstance() {
        return (PropertyTypeHandlerFacade) SessionUtility.findFacade(PropertyTypeHandlerFacade.class.getSimpleName()); 
    }
    
}
