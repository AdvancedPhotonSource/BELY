/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.settings;

import gov.anl.aps.logr.portal.controllers.ItemDomainLogbookController;
import gov.anl.aps.logr.portal.model.db.entities.EntitySetting;
import gov.anl.aps.logr.portal.model.db.entities.SettingEntity;
import gov.anl.aps.logr.portal.model.db.entities.SettingType;
import java.util.List;
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
    
    // Home page settings
    public static final String DisplayLogbookTypeId1Key = "ItemDomainLogbook.Home.EntityTypeId1";    
    public static final String DisplayLogbookTypeId2Key = "ItemDomainLogbook.Home.EntityTypeId2";    
    public static final String DisplayLogbookTypeId3Key = "ItemDomainLogbook.Home.EntityTypeId3";  
    
    protected Integer displayHomeLogbookTypeId1 = null;
    protected Integer displayHomeLogbookTypeId2 = null;
    protected Integer displayHomeLogbookTypeId3 = null;

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
        displayPropertyTypeId1 = parseSettingValueAsInteger(settingTypeMap.get(DisplayPropertyTypeId1SettingTypeKey).getDefaultValue());
        displayPropertyTypeId2 = parseSettingValueAsInteger(settingTypeMap.get(DisplayPropertyTypeId2SettingTypeKey).getDefaultValue());
        displayPropertyTypeId3 = parseSettingValueAsInteger(settingTypeMap.get(DisplayPropertyTypeId3SettingTypeKey).getDefaultValue());
        displayPropertyTypeId4 = parseSettingValueAsInteger(settingTypeMap.get(DisplayPropertyTypeId4SettingTypeKey).getDefaultValue());
        displayPropertyTypeId5 = parseSettingValueAsInteger(settingTypeMap.get(DisplayPropertyTypeId5SettingTypeKey).getDefaultValue());
        
        displayHomeLogbookTypeId1 = parseSettingValueAsInteger(settingTypeMap.get(DisplayLogbookTypeId1Key).getDefaultValue());        
        displayHomeLogbookTypeId2 = parseSettingValueAsInteger(settingTypeMap.get(DisplayLogbookTypeId2Key).getDefaultValue());        
        displayHomeLogbookTypeId3 = parseSettingValueAsInteger(settingTypeMap.get(DisplayLogbookTypeId3Key).getDefaultValue());        
    }

    public void resetLogbookHomeSettings(SettingEntity settingEntity) {
        List<EntitySetting> settingList = settingEntity.getSettingList();
        
        EntitySetting logbook1Setting = settingEntity.getSetting(DisplayLogbookTypeId1Key); 
        EntitySetting logbook2Setting = settingEntity.getSetting(DisplayLogbookTypeId2Key); 
        EntitySetting logbook3Setting = settingEntity.getSetting(DisplayLogbookTypeId3Key); 
        
        settingList.remove(logbook1Setting); 
        settingList.remove(logbook2Setting); 
        settingList.remove(logbook3Setting);               
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
        
        displayHomeLogbookTypeId1 = settingEntity.getSettingValueAsInteger(DisplayLogbookTypeId1Key, displayHomeLogbookTypeId1);
        displayHomeLogbookTypeId2 = settingEntity.getSettingValueAsInteger(DisplayLogbookTypeId2Key, displayHomeLogbookTypeId2);
        displayHomeLogbookTypeId3 = settingEntity.getSettingValueAsInteger(DisplayLogbookTypeId3Key, displayHomeLogbookTypeId3);
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
        
        settingEntity.setSettingValue(DisplayLogbookTypeId1Key, displayHomeLogbookTypeId1);
        settingEntity.setSettingValue(DisplayLogbookTypeId2Key, displayHomeLogbookTypeId2);
        settingEntity.setSettingValue(DisplayLogbookTypeId3Key, displayHomeLogbookTypeId3);
    }

    public Integer getDisplayHomeLogbookTypeId1() {
        return displayHomeLogbookTypeId1;
    }

    public void setDisplayHomeLogbookTypeId1(Integer displayHomeLogbookTypeId1) {
        this.displayHomeLogbookTypeId1 = displayHomeLogbookTypeId1;
    }

    public Integer getDisplayHomeLogbookTypeId2() {
        return displayHomeLogbookTypeId2;
    }

    public void setDisplayHomeLogbookTypeId2(Integer displayHomeLogbookTypeId2) {
        this.displayHomeLogbookTypeId2 = displayHomeLogbookTypeId2;
    }

    public Integer getDisplayHomeLogbookTypeId3() {
        return displayHomeLogbookTypeId3;
    }

    public void setDisplayHomeLogbookTypeId3(Integer displayHomeLogbookTypeId3) {
        this.displayHomeLogbookTypeId3 = displayHomeLogbookTypeId3;
    }

}
