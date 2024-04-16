/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.utilities;

import gov.anl.aps.logr.common.exceptions.CdbException;
import gov.anl.aps.logr.common.exceptions.InvalidObjectState;
import gov.anl.aps.logr.portal.constants.ItemDomainName;
import gov.anl.aps.logr.portal.constants.LogDocumentSettings;
import gov.anl.aps.logr.portal.model.db.beans.ItemDomainLogbookFacade;
import gov.anl.aps.logr.portal.model.db.entities.EntityInfo;
import gov.anl.aps.logr.portal.model.db.entities.EntityType;
import gov.anl.aps.logr.portal.model.db.entities.Item;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook;
import gov.anl.aps.logr.portal.model.db.entities.ItemElement;
import gov.anl.aps.logr.portal.model.db.entities.Log;
import gov.anl.aps.logr.portal.model.db.entities.PropertyValue;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
import gov.anl.aps.logr.portal.utilities.AuthorizationUtility;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 *
 * @author djarosz
 */
public class ItemDomainLogbookControllerUtility extends ItemControllerUtility<ItemDomainLogbook, ItemDomainLogbookFacade> {

    public final String SEARCH_OPT_KEY_ENTITY_TYPE_ID_LIST = "entity_type_id_list";
    public final String SEARCH_OPT_KEY_ITEM_TYPE_ID_LIST = "item_type_id_list";
    public final String SEARCH_OPT_KEY_START_TIME = "start_time";
    public final String SEARCH_OPT_KEY_END_TIME = "ent_time";

    @Override
    protected ItemDomainLogbookFacade getItemFacadeInstance() {
        return ItemDomainLogbookFacade.getInstance();
    }

    @Override
    protected ItemDomainLogbook instenciateNewItemDomainEntity() {
        return new ItemDomainLogbook();
    }

    @Override
    public boolean isEntityHasQrId() {
        return false;
    }

    @Override
    public boolean isEntityHasName() {
        return true;
    }

    @Override
    public boolean isEntityHasProject() {
        return false;
    }

    @Override
    public String getDefaultDomainName() {
        return ItemDomainName.logbook.getValue();
    }

    @Override
    public String getDerivedFromItemTitle() {
        throw new UnsupportedOperationException("Not supported yet."); // Generated from nbfs://nbhost/SystemFileSystem/Templates/Classes/Code/GeneratedMethodBody
    }

    @Override
    public String getEntityTypeName() {
        return "logbook";
    }

    // @Override
    public String getDisplayEntityTypeName() {
        return "Log Document";
    }

    @Override
    public boolean isEntityHasItemIdentifier2() {
        return false;
    }

    public ItemDomainLogbook completeCreateEntityInstance(ItemDomainLogbook newLogbookDoc, EntityType logbookType, UserInfo userInfo) throws CdbException, CloneNotSupportedException {
        return completeCreateEntityInstance(newLogbookDoc, logbookType, userInfo, true);
    }

    public ItemDomainLogbook completeCreateEntityInstance(ItemDomainLogbook newLogbookDoc, EntityType logbookType, UserInfo userInfo, boolean attachDefaultTemplate) throws CdbException, CloneNotSupportedException {
        newLogbookDoc.setEntityTypeList(new ArrayList<>());
        EntityType entityType = logbookType;
        newLogbookDoc.getEntityTypeList().add(entityType);

        if (attachDefaultTemplate) {
            Item primaryTemplateItem = entityType.getPrimaryTemplateItem();
            if (primaryTemplateItem != null) {
                ItemDomainLogbook templateToCreateNewItem = (ItemDomainLogbook) primaryTemplateItem;
                newLogbookDoc = completeSelectionOfTemplate(newLogbookDoc, templateToCreateNewItem, userInfo);
            }
        }

        return newLogbookDoc;
    }

    @Override
    protected void additionalSelectionOfTemplateSteps(ItemDomainLogbook item, ItemDomainLogbook templateItem, UserInfo user) throws CloneNotSupportedException {
        super.additionalSelectionOfTemplateSteps(item, templateItem, user);

        Boolean copyLogs = false;
        PropertyValue logbookSettingsProperty = item.getLogbookDocumentSettings();

        if (logbookSettingsProperty != null) {

            String logMode = logbookSettingsProperty.getPropertyMetadataValueForKey(LogDocumentSettings.logTemplateModeKey.getValue());
            if (logMode != null) {
                copyLogs = logMode.equals(LogDocumentSettings.logTemplateModeCopyVal.getValue());
            }
        }

        if (copyLogs) {
            copyLogs(templateItem, item);
        }

        // Ensure sort order is set. 
        List<ItemElement> templateElements = templateItem.getItemElementDisplayList();
        Float sortOrder = 0.0f;
        for (ItemElement templateElement : templateElements) {
            Float elementSortOrder = templateElement.getSortOrder();
            if (elementSortOrder != null) {
                sortOrder = elementSortOrder;
            }

            templateElement.setSortOrder(sortOrder);
            sortOrder += 1;
        }

        cloneCreateItemElements(item, templateItem, user, true, true, true);

        List<ItemElement> itemElementDisplayList = item.getItemElementDisplayList();
        for (ItemElement ie : itemElementDisplayList) {
            ItemDomainLogbook containedItem = (ItemDomainLogbook) ie.getContainedItem();
            ItemDomainLogbook newItem = null;

            newItem = (ItemDomainLogbook) containedItem.clone(user, user.getUserGroupList().get(0), false, false, false);

            newItem.getEntityTypeList().clear();
            newItem.setName(containedItem.getName());
            newItem.setItemIdentifier2(item.getViewUUID());

            if (copyLogs) {
                copyLogs(containedItem, newItem);
            }

            completeSelectionOfTemplate(newItem, containedItem, user);

            ie.setContainedItem(newItem);
        }
    }

    public ItemDomainLogbook createLogbookSectionItem(UserInfo user) throws CdbException {
        ItemDomainLogbook newSectionItem = createEntityInstance(user);

        if (newSectionItem.getIsItemTemplate()) {
            try {
                appendTemplateEntityType(newSectionItem);
            } catch (CdbException ex) {
                throw ex;
            }
        }

        return newSectionItem;
    }

    public ItemElement addLogbookSection(ItemDomainLogbook logDocument, ItemDomainLogbook newSection, UserInfo user) throws InvalidObjectState {
        // Verify logDocument is top level it is not allowed for sections to have sections. 
        List<ItemElement> itemElementMemberList = logDocument.getItemElementMemberList();
        if (!itemElementMemberList.isEmpty()) {
            throw new InvalidObjectState("Can only add sections to top level items.");
        }

        ItemElement newElement = createItemElement(logDocument, user);
        prepareAddItemElement(logDocument, newElement);

        // Ensure unique names per parent. 
        newSection.setItemIdentifier2("" + logDocument.getId());
        newElement.setContainedItem(newSection);

        return newElement;
    }

    @Override
    public Log prepareAddLog(ItemDomainLogbook cdbDomainEntity, UserInfo user) {
        Log log = super.prepareAddLog(cdbDomainEntity, user);

        log.setItemElementList(new ArrayList<>());
        ItemElement selfElement = cdbDomainEntity.getSelfElement();

        log.getItemElementList().add(selfElement);

        PropertyValue logbookDocumentSettings = cdbDomainEntity.getLogbookDocumentSettings();
        if (logbookDocumentSettings != null) {
            String templateMode = logbookDocumentSettings.getPropertyMetadataValueForKey(LogDocumentSettings.logTemplateModeKey.getValue());

            if (templateMode.equals(LogDocumentSettings.logTemplateModeTemplatePerEntryVal.getValue())) {
                Item createdFromTemplate = cdbDomainEntity.getCreatedFromTemplate();
                if (createdFromTemplate != null) {
                    List<Log> logList = createdFromTemplate.getLogList();
                    if (!logList.isEmpty()) {
                        Log templateLog = logList.get(0);
                        String templateText = templateLog.getText();
                        log.setText(templateText);
                    }
                }
            }
        }

        return log;
    }
    
    public void verifySaveLogLockoutsForItem(ItemDomainLogbook logDocument, Log log, UserInfo user) throws InvalidObjectState {
        // Ensure that top level document is checked for lockout. 
        logDocument = logDocument.getTopLevelLogDocument(); 
        
        // Use current for the lockout timeout especially for documents with sections.         
        EntityInfo entityInfo = logDocument.getEntityInfo();
        boolean isEntityWriteableByTimeout = entityInfo.refreshWriteableByTimeout();       
        boolean skipLockouts = (user.isUserAdmin() || user.isUserMaintainer());

        if (!skipLockouts) {
            if (isEntityWriteableByTimeout == false) {
                throw new InvalidObjectState("Log document is locked by lockout time.");
            }

            if (log != null) {
                Double logLockoutHours = logDocument.getLogLockoutHours();
                Date lastModifiedOnDateTime = log.getLastModifiedOnDateTime();

                boolean isWriteable = AuthorizationUtility.isEntityWriteableByTimeout(logLockoutHours, lastModifiedOnDateTime);
                if (!isWriteable) {
                    throw new InvalidObjectState("Log entry is locked by lockout time.");                                     
                }
            }
        }
    }
    

    public Map createAdvancedSearchMap(String entityTypeIdList, String itemTypeIdList, Date startTime, Date endTime) {
        /**
         * Generates the searchOpts for the searchEntities functionality. Can
         * also be used with CdbEntityController.performEntitySearch();
         */
        Map searchOpts = new HashMap<>();

        searchOpts.put(SEARCH_OPT_KEY_ENTITY_TYPE_ID_LIST, entityTypeIdList);
        searchOpts.put(SEARCH_OPT_KEY_ITEM_TYPE_ID_LIST, itemTypeIdList);
        searchOpts.put(SEARCH_OPT_KEY_START_TIME, startTime);
        searchOpts.put(SEARCH_OPT_KEY_END_TIME, endTime);

        return searchOpts;
    }

    @Override
    public List<ItemDomainLogbook> searchEntities(String searchString, Map searchOpts) {
        /**
         * search opts include the following keys: - entity_type_id (logbook
         * type id) - item_type_id (system id) - start_time (start modified date
         * search criteria) - end_time (end modified date search criteria)
         */
        if (searchOpts == null) {
            return searchEntities(searchString);
        }

        String entity_type_id_list = (String) searchOpts.get(SEARCH_OPT_KEY_ENTITY_TYPE_ID_LIST);
        String item_type_id_list = (String) searchOpts.get(SEARCH_OPT_KEY_ITEM_TYPE_ID_LIST);
        Date start_time = (Date) searchOpts.get(SEARCH_OPT_KEY_START_TIME);
        Date end_time = (Date) searchOpts.get(SEARCH_OPT_KEY_END_TIME);

        return getEntityDbFacade().searchEntitiesNoParent(searchString, item_type_id_list, entity_type_id_list, start_time, end_time);
    }

    @Override
    public List<ItemDomainLogbook> searchEntities(String searchString) {
        return getEntityDbFacade().searchEntitiesNoParent(searchString);
    }

    public static void copyLogs(ItemDomainLogbook oldLogDoc, ItemDomainLogbook newLogDoc) {
        List<Log> logList = oldLogDoc.getLogList();
        EntityInfo entityInfo = newLogDoc.getEntityInfo();
        UserInfo createdByUser = entityInfo.getCreatedByUser();

        Calendar calendar = Calendar.getInstance();

        for (Log log : logList) {
            String text = log.getText();
            Log newLog = newLogDoc.addLogEntry(text, createdByUser);

            // Specify creation date to maintain order. 
            calendar.add(Calendar.SECOND, 1);
            Date enteredTime = calendar.getTime();
            newLog.setEnteredOnDateTime(enteredTime);
        }
    }

}
