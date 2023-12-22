/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.settings;

import gov.anl.aps.logr.portal.controllers.ItemDomainLogbookController;
import gov.anl.aps.logr.portal.model.db.entities.SettingEntity;
import gov.anl.aps.logr.portal.model.db.entities.SettingType;
import java.util.Map;

/**
 *
 * @author djarosz
 */
public class ItemDomainLogbookSettings extends ItemSettings<ItemDomainLogbookController> {

    private static final String DisplayNumberOfItemsPerPageSettingTypeKey = "ItemDomainLogbook.List.Display.NumberOfItemsPerPage";
    private static final String DisplayIdSettingTypeKey = "ItemDomainLogbook.List.Display.Id";
    private static final String DisplayDescriptionSettingTypeKey = "ItemDomainLogbook.List.Display.Description";
    private static final String DisplayItemTypeSettingTypeKey = "ItemDomainLogbook.List.Display.ItemType";
    private static final String DisplayOwnerUserSettingTypeKey = "ItemDomainLogbook.List.Display.OwnerUser";
    private static final String DisplayOwnerGroupSettingTypeKey = "ItemDomainLogbook.List.Display.OwnerGroup";
    private static final String DisplayCreatedUserSettingTypeKey = "ItemDomainLogbook.List.Display.CreatedUser";
    private static final String DisplayCreatedTimeSettingTypeKey = "ItemDomainLogbook.List.Display.CreatedTime";
    private static final String DisplayModifiedByUserSettingTypeKey = "ItemDomainLogbook.List.Display.ModifiedByUser";
    private static final String DisplayModifiedTimeSettingTypeKey = "ItemDomainLogbook.List.Display.ModifiedTime";
    private static final String DisplayPropertyTypeId1SettingTypeKey = "ItemDomainLogbook.List.Display.PropertyTypeId1";
    private static final String DisplayPropertyTypeId2SettingTypeKey = "ItemDomainLogbook.List.Display.PropertyTypeId2";
    private static final String DisplayPropertyTypeId3SettingTypeKey = "ItemDomainLogbook.List.Display.PropertyTypeId3";
    private static final String DisplayPropertyTypeId4SettingTypeKey = "ItemDomainLogbook.List.Display.PropertyTypeId4";
    private static final String DisplayPropertyTypeId5SettingTypeKey = "ItemDomainLogbook.List.Display.PropertyTypeId5";

    public ItemDomainLogbookSettings(ItemDomainLogbookController parentController) {
        super(parentController);
        displayNumberOfItemsPerPage = 10;
    }
    
    @Override
    protected void updateSettingsFromSettingTypeDefaults(Map<String, SettingType> settingTypeMap) {
        super.updateSettingsFromSettingTypeDefaults(settingTypeMap);
        displayNumberOfItemsPerPage = Integer.valueOf(settingTypeMap.get(DisplayNumberOfItemsPerPageSettingTypeKey).getDefaultValue());
        displayId = Boolean.valueOf(settingTypeMap.get(DisplayIdSettingTypeKey).getDefaultValue());
        displayDescription = Boolean.valueOf(settingTypeMap.get(DisplayDescriptionSettingTypeKey).getDefaultValue());
        displayItemType = Boolean.valueOf(settingTypeMap.get(DisplayItemTypeSettingTypeKey).getDefaultValue());
        displayOwnerUser = Boolean.valueOf(settingTypeMap.get(DisplayOwnerUserSettingTypeKey).getDefaultValue());
        displayOwnerGroup = Boolean.valueOf(settingTypeMap.get(DisplayOwnerGroupSettingTypeKey).getDefaultValue());
        displayCreatedByUser = Boolean.valueOf(settingTypeMap.get(DisplayCreatedUserSettingTypeKey).getDefaultValue());
        displayCreatedOnDateTime = Boolean.valueOf(settingTypeMap.get(DisplayCreatedTimeSettingTypeKey).getDefaultValue());
        displayLastModifiedByUser = Boolean.valueOf(settingTypeMap.get(DisplayModifiedByUserSettingTypeKey).getDefaultValue());
        displayLastModifiedOnDateTime = Boolean.valueOf(settingTypeMap.get(DisplayModifiedTimeSettingTypeKey).getDefaultValue());
        displayPropertyTypeId1 = Integer.valueOf(settingTypeMap.get(DisplayPropertyTypeId1SettingTypeKey).getDefaultValue());
        displayPropertyTypeId2 = Integer.valueOf(settingTypeMap.get(DisplayPropertyTypeId2SettingTypeKey).getDefaultValue());
        displayPropertyTypeId3 = Integer.valueOf(settingTypeMap.get(DisplayPropertyTypeId3SettingTypeKey).getDefaultValue());
        displayPropertyTypeId4 = Integer.valueOf(settingTypeMap.get(DisplayPropertyTypeId4SettingTypeKey).getDefaultValue());
        displayPropertyTypeId5 = Integer.valueOf(settingTypeMap.get(DisplayPropertyTypeId5SettingTypeKey).getDefaultValue());
    }

    @Override
    protected void updateSettingsFromSessionSettingEntity(SettingEntity settingEntity) {
        super.updateSettingsFromSessionSettingEntity(settingEntity);
        displayNumberOfItemsPerPage = settingEntity.getSettingValueAsInteger(DisplayNumberOfItemsPerPageSettingTypeKey, displayNumberOfItemsPerPage);
        displayId = settingEntity.getSettingValueAsBoolean(DisplayIdSettingTypeKey, displayId);

        displayDescription = settingEntity.getSettingValueAsBoolean(DisplayDescriptionSettingTypeKey, displayDescription);
        displayItemType = settingEntity.getSettingValueAsBoolean(DisplayItemTypeSettingTypeKey, displayItemType);
        displayOwnerUser = settingEntity.getSettingValueAsBoolean(DisplayOwnerUserSettingTypeKey, displayOwnerUser);
        displayOwnerGroup = settingEntity.getSettingValueAsBoolean(DisplayOwnerGroupSettingTypeKey, displayOwnerGroup);
        displayCreatedByUser = settingEntity.getSettingValueAsBoolean(DisplayCreatedUserSettingTypeKey, displayCreatedByUser);
        displayCreatedOnDateTime = settingEntity.getSettingValueAsBoolean(DisplayCreatedTimeSettingTypeKey, displayCreatedOnDateTime);
        displayLastModifiedByUser = settingEntity.getSettingValueAsBoolean(DisplayModifiedByUserSettingTypeKey, displayLastModifiedByUser);
        displayLastModifiedOnDateTime = settingEntity.getSettingValueAsBoolean(DisplayModifiedTimeSettingTypeKey, displayLastModifiedOnDateTime);
        displayPropertyTypeId1 = settingEntity.getSettingValueAsInteger(DisplayPropertyTypeId1SettingTypeKey, displayPropertyTypeId1);
        displayPropertyTypeId2 = settingEntity.getSettingValueAsInteger(DisplayPropertyTypeId2SettingTypeKey, displayPropertyTypeId2);
        displayPropertyTypeId3 = settingEntity.getSettingValueAsInteger(DisplayPropertyTypeId3SettingTypeKey, displayPropertyTypeId3);
        displayPropertyTypeId4 = settingEntity.getSettingValueAsInteger(DisplayPropertyTypeId4SettingTypeKey, displayPropertyTypeId4);
        displayPropertyTypeId5 = settingEntity.getSettingValueAsInteger(DisplayPropertyTypeId5SettingTypeKey, displayPropertyTypeId5);            
    }

    @Override
    protected void saveSettingsForSessionSettingEntity(SettingEntity settingEntity) {
        super.saveSettingsForSessionSettingEntity(settingEntity);
        settingEntity.setSettingValue(DisplayNumberOfItemsPerPageSettingTypeKey, displayNumberOfItemsPerPage);
        settingEntity.setSettingValue(DisplayIdSettingTypeKey, displayId);

        settingEntity.setSettingValue(DisplayDescriptionSettingTypeKey, displayDescription);
        settingEntity.setSettingValue(DisplayItemTypeSettingTypeKey, displayItemType);
        settingEntity.setSettingValue(DisplayOwnerUserSettingTypeKey, displayOwnerUser);
        settingEntity.setSettingValue(DisplayOwnerGroupSettingTypeKey, displayOwnerGroup);
        settingEntity.setSettingValue(DisplayCreatedUserSettingTypeKey, displayCreatedByUser);
        settingEntity.setSettingValue(DisplayCreatedTimeSettingTypeKey, displayCreatedOnDateTime);
        settingEntity.setSettingValue(DisplayModifiedByUserSettingTypeKey, displayLastModifiedByUser);
        settingEntity.setSettingValue(DisplayModifiedTimeSettingTypeKey, displayLastModifiedOnDateTime);
        settingEntity.setSettingValue(DisplayPropertyTypeId1SettingTypeKey, displayPropertyTypeId1);
        settingEntity.setSettingValue(DisplayPropertyTypeId2SettingTypeKey, displayPropertyTypeId2);
        settingEntity.setSettingValue(DisplayPropertyTypeId3SettingTypeKey, displayPropertyTypeId3);
        settingEntity.setSettingValue(DisplayPropertyTypeId4SettingTypeKey, displayPropertyTypeId4);
        settingEntity.setSettingValue(DisplayPropertyTypeId5SettingTypeKey, displayPropertyTypeId5);  
    }

}
