/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.utilities;

import gov.anl.aps.logr.common.exceptions.CdbException;
import gov.anl.aps.logr.common.exceptions.InvalidObjectState;
import gov.anl.aps.logr.common.mqtt.model.LogEntryEvent;
import gov.anl.aps.logr.common.mqtt.model.ReplyLogEntryEvent;
import gov.anl.aps.logr.common.utilities.CollectionUtility;
import gov.anl.aps.logr.portal.constants.ItemDomainName;
import gov.anl.aps.logr.portal.constants.LogDocumentSettings;
import gov.anl.aps.logr.portal.model.db.beans.ItemDomainLogbookFacade;
import gov.anl.aps.logr.portal.model.db.entities.EntityInfo;
import gov.anl.aps.logr.portal.model.db.entities.EntityType;
import gov.anl.aps.logr.portal.model.db.entities.Item;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook;
import gov.anl.aps.logr.portal.model.db.entities.ItemElement;
import gov.anl.aps.logr.portal.model.db.entities.ItemType;
import gov.anl.aps.logr.portal.model.db.entities.Log;
import gov.anl.aps.logr.portal.model.db.entities.PropertyValue;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
import gov.anl.aps.logr.portal.utilities.AuthorizationUtility;
import gov.anl.aps.logr.portal.utilities.SearchResult;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 *
 * @author djarosz
 */
public class ItemDomainLogbookControllerUtility extends ItemControllerUtility<ItemDomainLogbook, ItemDomainLogbookFacade> {

    public final String SEARCH_OPT_KEY_ENTITY_TYPE_LIST = "entity_type_list";
    public final String SEARCH_OPT_KEY_ITEM_TYPE_LIST = "item_type_list";
    public final String SEARCH_OPT_KEY_USER_LIST = "user_list";
    public final String SEARCH_OPT_KEY_START_MODIFIED_TIME = "start_modified_time";
    public final String SEARCH_OPT_KEY_END_MODIFIED_TIME = "ent_modified_time";
    public final String SEARCH_OPT_KEY_START_CREATED_TIME = "start_created_time";
    public final String SEARCH_OPT_KEY_END_CREATED_TIME = "ent_created_time";

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

        // Verify if existing section with same name. 
        String sectionName = newSection.getName();
        for (ItemElement ie : logDocument.getItemElementDisplayList()) {
            Item containedItem = ie.getContainedItem();
            if (containedItem.getName().equals(sectionName)) {
                throw new InvalidObjectState(String.format("Section with name '%s' already exists.", sectionName));
            }
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

            if (templateMode != null && templateMode.equals(LogDocumentSettings.logTemplateModeTemplatePerEntryVal.getValue())) {
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

    public Map createAdvancedSearchMap(
            List<EntityType> entityTypeList,
            List<ItemType> itemTypeList,
            List<UserInfo> userList,
            Date startModifiedTime, Date endModifiedTime,
            Date startCreatedTime, Date endCreatedTime) {
        /**
         * Generates the searchOpts for the searchEntities functionality. Can
         * also be used with CdbEntityController.performEntitySearch();
         */
        Map searchOpts = new HashMap<>();

        searchOpts.put(SEARCH_OPT_KEY_ENTITY_TYPE_LIST, entityTypeList);
        searchOpts.put(SEARCH_OPT_KEY_ITEM_TYPE_LIST, itemTypeList);
        searchOpts.put(SEARCH_OPT_KEY_USER_LIST, userList);
        searchOpts.put(SEARCH_OPT_KEY_START_MODIFIED_TIME, startModifiedTime);
        searchOpts.put(SEARCH_OPT_KEY_END_MODIFIED_TIME, endModifiedTime);
        searchOpts.put(SEARCH_OPT_KEY_START_CREATED_TIME, startCreatedTime);
        searchOpts.put(SEARCH_OPT_KEY_END_CREATED_TIME, endCreatedTime);

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

        List<EntityType> entityTypeList = (List<EntityType>) searchOpts.get(SEARCH_OPT_KEY_ENTITY_TYPE_LIST);
        List<ItemType> itemTypeList = (List<ItemType>) searchOpts.get(SEARCH_OPT_KEY_ITEM_TYPE_LIST);
        List<UserInfo> userList = (List<UserInfo>) searchOpts.get(SEARCH_OPT_KEY_USER_LIST);

        String entity_type_id_list = (String) CollectionUtility.generateIdListString(entityTypeList);
        String item_type_id_list = (String) CollectionUtility.generateIdListString(itemTypeList);
        String user_id_list = (String) CollectionUtility.generateIdListString(userList);
        Date start_modified_time = (Date) searchOpts.get(SEARCH_OPT_KEY_START_MODIFIED_TIME);
        Date end_modified_time = (Date) searchOpts.get(SEARCH_OPT_KEY_END_MODIFIED_TIME);
        Date start_created_time = (Date) searchOpts.get(SEARCH_OPT_KEY_START_CREATED_TIME);
        Date end_created_time = (Date) searchOpts.get(SEARCH_OPT_KEY_END_CREATED_TIME);

        return getEntityDbFacade().searchEntitiesNoParent(
                searchString, item_type_id_list,
                entity_type_id_list, user_id_list,
                start_modified_time, end_modified_time,
                start_created_time, end_created_time);
    }

    @Override
    public List<ItemDomainLogbook> searchEntities(String searchString) {
        return getEntityDbFacade().searchEntitiesNoParent(searchString);
    }

    @Override
    public LinkedList<SearchResult> performEntitySearch(String searchString, Map searchOpts, boolean caseInsensitive) {
        LinkedList<SearchResult> searchResultList = super.performEntitySearch(searchString, searchOpts, caseInsensitive);

        List<EntityType> searchEntityTypeList = (List<EntityType>) searchOpts.get(SEARCH_OPT_KEY_ENTITY_TYPE_LIST);
        List<ItemType> searchItemTypeList = (List<ItemType>) searchOpts.get(SEARCH_OPT_KEY_ITEM_TYPE_LIST);
        List<UserInfo> searchUserList = (List<UserInfo>) searchOpts.get(SEARCH_OPT_KEY_USER_LIST);

        Date start_modified_time = (Date) searchOpts.get(SEARCH_OPT_KEY_START_MODIFIED_TIME);
        Date end_modified_time = (Date) searchOpts.get(SEARCH_OPT_KEY_END_MODIFIED_TIME);
        Date start_created_time = (Date) searchOpts.get(SEARCH_OPT_KEY_START_CREATED_TIME);
        Date end_created_time = (Date) searchOpts.get(SEARCH_OPT_KEY_END_CREATED_TIME);

        // Add search opts to match description. 
        for (SearchResult result : searchResultList) {
            addCommonLogEntryDocumentMatches(result, searchEntityTypeList, searchItemTypeList);

            ItemDomainLogbook resultItem = (ItemDomainLogbook) result.getCdbEntity();
            EntityInfo entityInfo = resultItem.getEntityInfo();

            if (searchUserList != null && !searchUserList.isEmpty()) {
                for (UserInfo ui : searchUserList) {
                    Integer searchUserId = ui.getId();

                    UserInfo ownerUser = entityInfo.getOwnerUser();
                    UserInfo createdByUser = entityInfo.getCreatedByUser();
                    UserInfo lastModifiedByUser = entityInfo.getLastModifiedByUser();

                    if (Objects.equals(ownerUser.getId(), searchUserId)) {
                        result.addAttributeMatch("Owner User", ownerUser.toString());
                    }
                    if (Objects.equals(createdByUser.getId(), searchUserId)) {
                        result.addAttributeMatch("Create User", createdByUser.toString());
                    }
                    if (Objects.equals(lastModifiedByUser.getId(), searchUserId)) {
                        result.addAttributeMatch("Last Modify User", lastModifiedByUser.toString());
                    }
                }
            }

            if (start_created_time != null || end_created_time != null) {
                Date createdOnDateTime = entityInfo.getCreatedOnDateTime();
                result.addAttributeMatch("Created on", createdOnDateTime.toString());
            }

            if (start_modified_time != null || end_modified_time != null) {
                Date modifiedOnDateTime = entityInfo.getLastModifiedOnDateTime();
                result.addAttributeMatch("Modified on", modifiedOnDateTime.toString());
            }

        }

        return searchResultList;
    }

    public void addCommonLogEntryDocumentMatches(SearchResult result, List<EntityType> searchEntityTypeList, List<ItemType> searchItemTypeList) {
        ItemDomainLogbook resultItem = (ItemDomainLogbook) result.getCdbEntity();
        if (searchEntityTypeList != null && !searchEntityTypeList.isEmpty()) {
            List<EntityType> etList = resultItem.getEntityTypeList();

            for (EntityType et : searchEntityTypeList) {
                for (EntityType resultEt : etList) {
                    if (Objects.equals(et.getId(), resultEt.getId())) {
                        result.addAttributeMatch("Logbook", et.getLongDisplayName());
                    }
                }
            }
        }

        if (searchItemTypeList != null && !searchItemTypeList.isEmpty()) {
            List<ItemType> itList = resultItem.getItemTypeList();

            for (ItemType it : searchItemTypeList) {
                for (ItemType resultIt : itList) {
                    if (Objects.equals(it.getId(), resultIt.getId())) {
                        result.addAttributeMatch("System", it.getName());
                    }
                }
            }
        }
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

    private ItemDomainLogbook getParentLogbook(Log logEntry) {
        Log parentLog = logEntry.getParentLog();

        if (parentLog != null) {
            // Parent log has association to the log document.
            logEntry = parentLog;
        }
        List<ItemElement> itemElementList = logEntry.getItemElementList();

        if (itemElementList != null && itemElementList.size() == 1) {
            // This should always happen.
            // No exception however since this is required for notification framework not core functionality.
            ItemElement parentElement = itemElementList.get(0);
            Item parentItem = parentElement.getParentItem();
            if (parentItem instanceof ItemDomainLogbook) {
                return (ItemDomainLogbook) parentItem;
            }
        }
        return null;

    }

    private String getLogDiffString(Log originalLog, Log updatedLog) {
        String originalText;
        String updatedText = updatedLog.getText();

        if (originalLog != null) {
            originalText = originalLog.getText();
        } else {
            return updatedText;
        }

        StringBuilder diffOutput = new StringBuilder();
        String[] originalLines = originalText.split("\n");
        String[] updatedLines = updatedText.split("\n");

        int maxLines = Math.max(originalLines.length, updatedLines.length);

        for (int i = 0; i < maxLines; i++) {
            String originalLine = i < originalLines.length ? originalLines[i] : "";
            String updatedLine = i < updatedLines.length ? updatedLines[i] : "";

            if (!originalLine.equals(updatedLine)) {
                if (i < originalLines.length) {
                    diffOutput.append("- ").append(originalLine).append("\n");
                }
                if (i < updatedLines.length) {
                    diffOutput.append("+ ").append(updatedLine).append("\n");
                }
            } else if (i < originalLines.length) {
                diffOutput.append("  ").append(originalLine).append("\n");
            }
        }
        return diffOutput.toString();

    }

    public Log saveLog(Log logEntity, UserInfo user, Log originalLog) throws CdbException {
        LogControllerUtility utility = new LogControllerUtility();

        String logDiffString = getLogDiffString(originalLog, logEntity);

        // Avoid duplicates
        logEntity.clearActionEvents();

        ItemDomainLogbook parentLogbook = getParentLogbook(logEntity);

        Log parentLog = logEntity.getParentLog();
        Integer id = logEntity.getId();

        String description = "";
        if (id == null) {
            description += "log entry was added";
        } else {
            description += "log entry id [" + id + "] was modified";
        }

        if (parentLog != null) {
            description = "reply " + description;

            // Reply
            logEntity.addActionEvent(new ReplyLogEntryEvent(parentLogbook, logEntity, user, description, logDiffString));
        } else {
            logEntity.addActionEvent(new LogEntryEvent(parentLogbook, logEntity, user, description, logDiffString));
        }

        // Add a generic log entry.
        return utility.saveLogEntry(logEntity, user);
    }

}
