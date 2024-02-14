/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.beans;

import gov.anl.aps.logr.portal.model.db.entities.EntityType;
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
public class EntityTypeFacade extends CdbEntityFacade<EntityType> {

    @PersistenceContext(unitName = "LogrPortalPU")
    private EntityManager em;

    @Override
    protected EntityManager getEntityManager() {
        return em;
    }

    public EntityTypeFacade() {
        super(EntityType.class);
    }
    
    public EntityType findByName(String name) {
        try{
            return (EntityType) em.createNamedQuery("EntityType.findByName")
                    .setParameter("name", name)
                    .getSingleResult();
        } catch (NoResultException ex) {
            
        }
        return null;
    }
    
    public List<EntityType> findTopLevelByDomain(Integer domainId) { 
        try{
            return (List<EntityType>) em.createNamedQuery("EntityType.findTopLevelByDomain")
                    .setParameter("allowedDomainId", domainId)
                    .getResultList();
        } catch (NoResultException ex) {
            
        }
        return null;
        
    }
    
    
    
    public static EntityTypeFacade getInstance() {
        return (EntityTypeFacade) SessionUtility.findFacade(EntityTypeFacade.class.getSimpleName()); 
    }
    
}
