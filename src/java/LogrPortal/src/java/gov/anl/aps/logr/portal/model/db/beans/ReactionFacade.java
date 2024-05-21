/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.beans;

import gov.anl.aps.logr.portal.model.db.entities.Reaction;
import gov.anl.aps.logr.portal.utilities.SessionUtility;
import java.util.List;
import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;

/**
 * Reaction facade facilitates communication to db for the reaction table. 
 * 
 * @author djarosz
 */
@Stateless
public class ReactionFacade extends CdbEntityFacade<Reaction> {

    @PersistenceContext(unitName = "LogrPortalPU")
    private EntityManager em;

    @Override
    protected EntityManager getEntityManager() {
        return em;
    }

    public ReactionFacade() {
        super(Reaction.class);
    }

    public static ReactionFacade getInstance() {
        return (ReactionFacade) SessionUtility.findFacade(ReactionFacade.class.getSimpleName());
    }

    public List<Reaction> findAll() {
        return (List<Reaction>) em.createNamedQuery("Reaction.findAllSorted")
                .getResultList();
    }

}
