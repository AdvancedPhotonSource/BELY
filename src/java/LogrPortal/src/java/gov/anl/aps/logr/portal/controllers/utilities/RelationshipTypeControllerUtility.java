/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.utilities;

import gov.anl.aps.logr.common.exceptions.CdbException;
import gov.anl.aps.logr.portal.model.db.beans.RelationshipTypeFacade;
import gov.anl.aps.logr.portal.model.db.entities.RelationshipType;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;

/**
 *
 * @author darek
 */
public class RelationshipTypeControllerUtility extends CdbEntityControllerUtility<RelationshipType, RelationshipTypeFacade> {
    
    public RelationshipType createRelationshipTypeWithName(String relationshipTypeName, UserInfo userInfo) throws CdbException {
        RelationshipType relationshipType = createEntityInstance(userInfo);
        relationshipType.setName(relationshipTypeName);
        create(relationshipType, userInfo); 
        return relationshipType; 
    }

    @Override
    protected RelationshipTypeFacade getEntityDbFacade() {
        return RelationshipTypeFacade.getInstance();
    }
    
    @Override
    public String getEntityTypeName() {
        return "relationshipType";
    }

    @Override
    public RelationshipType createEntityInstance(UserInfo sessionUser) {
        return new RelationshipType();
    }
    
}
