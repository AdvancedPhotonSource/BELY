/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.beans;

import gov.anl.aps.logr.portal.model.db.entities.SettingType;
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
public class SettingTypeFacade extends CdbEntityFacade<SettingType> {

    @PersistenceContext(unitName = "LogrPortalPU")
    private EntityManager em;

    @Override
    protected EntityManager getEntityManager() {
        return em;
    }

    public SettingTypeFacade() {
        super(SettingType.class);
    }

    public SettingType findByName(String name) {
        try {
            return (SettingType) em.createNamedQuery("SettingType.findByName")
                    .setParameter("name", name)
                    .getSingleResult();
        } catch (NoResultException ex) {

        }
        return null;
    }

    public static SettingTypeFacade getInstance() {
        return (SettingTypeFacade) SessionUtility.findFacade(SettingTypeFacade.class.getSimpleName());
    }

}
