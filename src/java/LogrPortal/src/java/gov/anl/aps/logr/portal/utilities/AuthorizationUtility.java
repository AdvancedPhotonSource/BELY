/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.utilities;

import gov.anl.aps.logr.portal.model.db.entities.CdbEntity;
import gov.anl.aps.logr.portal.model.db.entities.EntityInfo;
import gov.anl.aps.logr.portal.model.db.entities.UserGroup;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
import java.time.Duration;
import java.time.Instant;
import java.util.Date;

/**
 * Utility for handling user authorization for manipulating CDB entities.
 */
public class AuthorizationUtility {

    public static boolean isEntityWriteableByUser(EntityInfo entityInfo, UserInfo userInfo) {
        boolean entityWriteableByUserBase = isEntityWriteableByUserBase(entityInfo, userInfo);

        if (!entityWriteableByUserBase) {
            return entityWriteableByUserBase;
        }

        return entityInfo.isEntityWriteableByTimeout();
    }

    private static boolean isEntityWriteableByUserBase(EntityInfo entityInfo, UserInfo userInfo) {
        // Users can write object if entityInfo != null and:
        // current user is owner, or the object is writeable by owner group
        // and current user is member of that group
        if (entityInfo == null || userInfo == null) {
            return false;
        }

        UserInfo ownerUser = entityInfo.getOwnerUser();
        if (ownerUser != null && ownerUser.getId().equals(userInfo.getId())) {
            return true;
        }

        Boolean isGroupWriteable = entityInfo.getIsGroupWriteable();
        if (isGroupWriteable == null || !isGroupWriteable.booleanValue()) {
            return false;
        }

        UserGroup ownerUserGroup = entityInfo.getOwnerUserGroup();
        if (ownerUserGroup == null) {
            return false;
        }

        for (UserGroup userGroup : userInfo.getUserGroupList()) {
            if (ownerUserGroup.getId().equals(userGroup.getId())) {
                return true;
            }
        }
        return false;
    }

    public static <EntityType extends CdbEntity> boolean isEntityWriteableByUser(EntityType entity, UserInfo userInfo) {
        Object entityInfo = entity.getEntityInfo();
        if (entityInfo instanceof EntityInfo) {
            return isEntityWriteableByUser((EntityInfo) entityInfo, userInfo);
        }
        return false;
    }

    public static boolean isEntityWriteableByTimeout(Double lockoutTimeInHours, Date createdOnDateTime) {
        if (lockoutTimeInHours != null && lockoutTimeInHours > 0) {
            Instant createdTime = createdOnDateTime.toInstant();
            Instant now = Instant.now();

            Duration diff = Duration.between(createdTime, now);

            long minuteSinceCreation = diff.toMinutes();
            minuteSinceCreation -= 3;
            double timoutMinutes = lockoutTimeInHours * 60;

            return minuteSinceCreation < timoutMinutes;
        }
        
        return true; 
    }

}
