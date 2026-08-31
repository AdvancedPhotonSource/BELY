/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.beans;

import gov.anl.aps.logr.portal.constants.EntityTypeName;
import gov.anl.aps.logr.portal.constants.ItemDomainName;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook;
import gov.anl.aps.logr.portal.utilities.SessionUtility;
import javax.ejb.Stateless;
import javax.persistence.NoResultException;

/**
 *
 * @author djarosz
 */
@Stateless
public class ItemDomainLogbookFacade extends ItemFacadeBase<ItemDomainLogbook> {

    public ItemDomainLogbookFacade() {
        super(ItemDomainLogbook.class);
    }

    @Override
    public ItemDomainName getDomain() {
        return ItemDomainName.logbook;
    }

    public ItemDomainLogbook getPreviousLogDocument(String entityTypeName, Integer currentId) {
        try {
            ItemDomainName domain = getDomain();
            String domainValue = domain.getValue();
            return (ItemDomainLogbook) em.createNamedQuery("Item.findByDomainNameAndEntityTypeAndTopLevelBeforeId")
                    .setParameter("domainName", domainValue)
                    .setParameter("entityTypeName", entityTypeName)
                    .setParameter("itemId", currentId)
                    .setMaxResults(1)
                    .getSingleResult();
        } catch (NoResultException ex) {
        }
        return null;
    }

    public ItemDomainLogbook getNextLogDocument(String entityTypeName, Integer currentId) {
        try {
            ItemDomainName domain = getDomain();
            String domainValue = domain.getValue();
            return (ItemDomainLogbook) em.createNamedQuery("Item.findByDomainNameAndEntityTypeAndTopLevelAfterId")
                    .setParameter("domainName", domainValue)
                    .setParameter("entityTypeName", entityTypeName)
                    .setParameter("itemId", currentId)
                    .setMaxResults(1)
                    .getSingleResult();
        } catch (NoResultException ex) {
        }
        return null;

    }

    // Previous top level log document across every logbook type, excluding templates. 
    public ItemDomainLogbook getPreviousLogDocument(Integer currentId) {
        try {
            return (ItemDomainLogbook) em.createNamedQuery("Item.findByDomainNameAndTopLevelBeforeId")
                    .setParameter("domainName", getDomain().getValue())
                    .setParameter("excludeEntityTypeName", EntityTypeName.template.getValue())
                    .setParameter("itemId", currentId)
                    .setMaxResults(1)
                    .getSingleResult();
        } catch (NoResultException ex) {
        }
        return null;
    }

    // Next top level log document across every logbook type, excluding templates. 
    public ItemDomainLogbook getNextLogDocument(Integer currentId) {
        try {
            return (ItemDomainLogbook) em.createNamedQuery("Item.findByDomainNameAndTopLevelAfterId")
                    .setParameter("domainName", getDomain().getValue())
                    .setParameter("excludeEntityTypeName", EntityTypeName.template.getValue())
                    .setParameter("itemId", currentId)
                    .setMaxResults(1)
                    .getSingleResult();
        } catch (NoResultException ex) {
        }
        return null;
    }

    public static ItemDomainLogbookFacade getInstance() {
        return (ItemDomainLogbookFacade) SessionUtility.findFacade(ItemDomainLogbookFacade.class.getSimpleName());
    }

}
