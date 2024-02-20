/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers;

import gov.anl.aps.logr.common.exceptions.CdbException;
import gov.anl.aps.logr.portal.constants.EntityTypeName;
import gov.anl.aps.logr.portal.controllers.extensions.ItemCreateWizardController;
import gov.anl.aps.logr.portal.controllers.extensions.ItemCreateWizardDomainLogbookController;
import gov.anl.aps.logr.portal.controllers.settings.ItemDomainLogbookSettings;
import gov.anl.aps.logr.portal.controllers.utilities.EntityInfoControllerUtility;
import gov.anl.aps.logr.portal.controllers.utilities.EntityTypeControllerUtility;
import gov.anl.aps.logr.portal.controllers.utilities.ItemDomainLogbookControllerUtility;
import gov.anl.aps.logr.portal.controllers.utilities.PropertyTypeControllerUtility;
import gov.anl.aps.logr.portal.model.ItemDomainLogbookLazyDataModel;
import gov.anl.aps.logr.portal.model.db.beans.ItemDomainLogbookFacade;
import gov.anl.aps.logr.portal.model.db.beans.LogFacade;
import gov.anl.aps.logr.portal.model.db.entities.Domain;
import gov.anl.aps.logr.portal.model.db.entities.EntityInfo;
import gov.anl.aps.logr.portal.model.db.entities.EntityType;
import gov.anl.aps.logr.portal.model.db.entities.Item;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook;
import gov.anl.aps.logr.portal.model.db.entities.ItemElement;
import gov.anl.aps.logr.portal.model.db.entities.Log;
import gov.anl.aps.logr.portal.model.db.entities.PropertyType;
import gov.anl.aps.logr.portal.model.db.entities.PropertyValue;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
import gov.anl.aps.logr.portal.model.db.utilities.EntityInfoUtility;
import gov.anl.aps.logr.portal.utilities.AuthorizationUtility;
import gov.anl.aps.logr.portal.utilities.MarkdownParser;
import gov.anl.aps.logr.portal.utilities.SearchResult;
import gov.anl.aps.logr.portal.utilities.SessionUtility;
import java.io.IOException;
import java.time.DayOfWeek;
import java.time.LocalDateTime;
import java.time.Month;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.List;
import java.util.Objects;
import java.util.regex.Pattern;
import javax.ejb.EJB;
import javax.enterprise.context.SessionScoped;
import javax.faces.component.UIComponent;
import javax.faces.context.FacesContext;
import javax.faces.convert.Converter;
import javax.faces.convert.FacesConverter;
import javax.faces.model.DataModel;
import javax.faces.model.ListDataModel;
import javax.inject.Named;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

/**
 * Controller that provides functionality to create, edit, delete, and view
 * logbook documents and its related data such as log entries.
 *
 * @author djarosz
 */
@Named(ItemDomainLogbookController.controllerNamed)
@SessionScoped
public class ItemDomainLogbookController extends ItemController<ItemDomainLogbookControllerUtility, ItemDomainLogbook, ItemDomainLogbookFacade, ItemDomainLogbookSettings, ItemDomainLogbookLazyDataModel> {

    private static final Logger logger = LogManager.getLogger(ItemDomainLogbookController.class.getName());

    @EJB
    ItemDomainLogbookFacade itemDomainLogbookFacade;

    @EJB
    LogFacade logFacade;

    private EntityType currentEntityType = null;
    private Log lastLog;

    private List<SearchResult> logResults;
    private List<EntityType> logbookEntityTypes;
    private List<EntityType> topLevelEntityTypeList;

    private EntityInfoControllerUtility entityInfoControllerUtility;

    private static final String OPS_ENTITY_TYPE_NAME = "ops";

    private static final String LOGBOOK_SETTINGS_SHOW_TIMESTAMP_KEY = "showTimestamps";
    private static final String LOGBOOK_SETTINGS_TEMPLATE_LOG_MODE_KEY = "logMode";
    private static final String LOGBOOK_SETTINGS_TEMPLATE_LOG_MODE_NONE_VAL = "none";
    private static final String LOGBOOK_SETTINGS_TEMPLATE_LOG_MODE_COPY_VAL = "copy";
    private static final String LOGBOOK_SETTINGS_TEMPLATE_LOG_MODE_TEMPLATE_VAL = "template per entry";

    // Custom operations functionality.. 
    // <editor-fold defaultstate="collapsed" desc="Operations specific variables.">
    private static final String OPS_TEMPLATE_NAME = "Operations Shift";
    private static final String OPS_GENERAL_FIRST_LOG_ENTRY = "Personnel: %s\n\nShift Type: %s";

    private static final String OPS_SHIFT_START_PROPERTY_TYPE_NAME = "Shift Start";
    private static final String OPS_SHIFT_END_PROPERTY_TYPE_NAME = "Shift End";
    private static final String OPS_PERSONNEL_PROPERTY_TYPE_NAME = "Personnel";
    private static final String OPS_SHIFT_TYPE_PROPERTY_TYPE_NAME = "Shift Type";

    private static final DateTimeFormatter dayFormatter = DateTimeFormatter.ofPattern("EEEE");
    private static final DateTimeFormatter dateFormatter = DateTimeFormatter.ofPattern("MMMM dd, yyyy");
    private static final DateTimeFormatter dayYearNumFormatter = DateTimeFormatter.ofPattern("dd, yyyy");
    private static final DateTimeFormatter shortDateFormatter = DateTimeFormatter.ofPattern("MMMM dd");
    private static final DateTimeFormatter timeFormatter = DateTimeFormatter.ofPattern("HH:mm");

    private static final int[] COPY_OPS_SHIFT_SECTIONS_INX = new int[]{5};
    private boolean initialOpsSelectionReset;
    private List<String> opsSectionCopyList = null;
    private List<String> opsSelectedCopyList = null;

    // </editor-fold>
    public final static String controllerNamed = "itemDomainLogbookController";

    public static ItemDomainLogbookController getInstance() {
        return (ItemDomainLogbookController) SessionUtility.findBean(controllerNamed);
    }

    @Override
    public ItemDomainLogbookLazyDataModel createItemLazyDataModel() {
        return new ItemDomainLogbookLazyDataModel(itemDomainLogbookFacade, getDefaultDomain(), settingObject);
    }

    @Override
    protected ItemDomainLogbookControllerUtility createControllerUtilityInstance() {
        return new ItemDomainLogbookControllerUtility();
    }

    @Override
    protected ItemDomainLogbookSettings createNewSettingObject() {
        return new ItemDomainLogbookSettings(this);
    }

    @Override
    protected ItemCreateWizardController getItemCreateWizardController() {
        return ItemCreateWizardDomainLogbookController.getInstance();
    }

    @Override
    public String getCreateDisplayEntityTypeName() {
        if (currentEntityType != null) {
            String displayName = currentEntityType.getDisplayName();
            return String.format("%s %s", displayName, getDisplayEntityTypeName());
        }

        return super.getCreateDisplayEntityTypeName();
    }

    @Override
    public List<ItemDomainLogbook> getTemplatesList() {
        if (templatesList == null) {
            templatesList = getEntityDbFacade().findByDomainAndEntityTypeAndTopLevel(getDefaultDomainName(), EntityTypeName.template.getValue());
        }
        return templatesList;
    }

    @Override
    public DataModel getTemplateItemsListDataModel() {
        if (templateItemsListDataModel == null) {
            List<ItemDomainLogbook> templatesList = getTemplatesList();
            templateItemsListDataModel = new ListDataModel(templatesList);
        }
        return templateItemsListDataModel;
    }

    @Override
    protected ItemDomainLogbookFacade getEntityDbFacade() {
        return itemDomainLogbookFacade;
    }

    @Override
    public boolean getEntityDisplayItemConnectors() {
        return false;
    }

    @Override
    public boolean getEntityDisplayDerivedFromItem() {
        return false;
    }

    @Override
    public boolean getEntityDisplayItemGallery() {
        return true;
    }

    @Override
    public boolean getEntityDisplayItemLogs() {
        return true;
    }

    @Override
    public boolean getEntityDisplayItemSources() {
        return false;
    }

    @Override
    public boolean getEntityDisplayItemProperties() {
        return true;
    }

    @Override
    public boolean getEntityDisplayItemElements() {
        return true;
    }

    @Override
    public boolean getEntityDisplayItemsDerivedFromItem() {
        return false;
    }

    @Override
    public boolean getEntityDisplayTemplates() {
        return true;
    }

    @Override
    public boolean getRenderItemElementList() {
        return true;
    }

    @Override
    public boolean getEntityDisplayItemMemberships() {
        return false;
    }

    @Override
    public boolean getEntityDisplayItemEntityTypes() {
        return false;
    }

    @Override
    public String getStyleName() {
        return "logbook";
    }

    private EntityInfoControllerUtility getEntityInfoControllerUtility() {
        if (entityInfoControllerUtility == null) {
            entityInfoControllerUtility = new EntityInfoControllerUtility();
        }

        return entityInfoControllerUtility;
    }

    @Override
    public String getDefaultDomainDerivedFromDomainName() {
        throw new UnsupportedOperationException("Not supported yet."); // Generated from nbfs://nbhost/SystemFileSystem/Templates/Classes/Code/GeneratedMethodBody
    }

    @Override
    public String getDefaultDomainDerivedToDomainName() {
        throw new UnsupportedOperationException("Not supported yet."); // Generated from nbfs://nbhost/SystemFileSystem/Templates/Classes/Code/GeneratedMethodBody
    }

    @Override
    public String getItemsDerivedFromItemTitle() {
        throw new UnsupportedOperationException("Not supported yet."); // Generated from nbfs://nbhost/SystemFileSystem/Templates/Classes/Code/GeneratedMethodBody
    }

    @Override
    public boolean entityCanBeCreatedByUsers() {
        return true;
    }

    public Double getLogLockoutHours() {
        ItemDomainLogbook current = getCurrent();
        return current.getLogLockoutHours();
    }

    public void setLogLockoutHours(Double hours) {
        if (hours == null) {
            hours = 0.0;
        }
        String LOG_LOCKOUT_SETTING_KEY = ItemDomainLogbook.LOG_LOCKOUT_SETTING_KEY;

        ItemDomainLogbook current = getCurrent();
        current.setLogLockoutHours(hours);
        setLogbookSettingPropertyKey(LOG_LOCKOUT_SETTING_KEY, hours.toString());
    }

    public Double getDocumentLockoutHours() {
        ItemDomainLogbook current = getCurrent();
        return current.getDocumentLockoutHours();
    }

    public void setDocumentLockoutHours(Double hours) {
        if (hours == null) {
            hours = 0.0;
        }
        String DOC_LOCKOUT_SETTING_KEY = ItemDomainLogbook.DOC_LOCKOUT_SETTING_KEY;

        ItemDomainLogbook current = getCurrent();
        current.setDocumentLockoutHours(hours);
        setLogbookSettingPropertyKey(DOC_LOCKOUT_SETTING_KEY, hours.toString());
    }

    public boolean getLogbookDisplayTimestamps() {
        return getLogbookSettingBoolean(true, LOGBOOK_SETTINGS_SHOW_TIMESTAMP_KEY);
    }

    public void setLogbookDisplayTimestamps(boolean displayTimestamp) {
        String value = String.valueOf(displayTimestamp);
        setLogbookSettingPropertyKey(LOGBOOK_SETTINGS_SHOW_TIMESTAMP_KEY, value);
    }

    public String getLogbookTemplateLogMode() {
        return getLogbookSetting(LOGBOOK_SETTINGS_TEMPLATE_LOG_MODE_NONE_VAL, LOGBOOK_SETTINGS_TEMPLATE_LOG_MODE_KEY);
    }

    public void setLogbookTemplateLogMode(String logMode) {
        setLogbookSettingPropertyKey(LOGBOOK_SETTINGS_TEMPLATE_LOG_MODE_KEY, logMode);
    }

    public String getLOGBOOK_SETTINGS_TEMPLATE_LOG_MODE_NONE_VAL() {
        return LOGBOOK_SETTINGS_TEMPLATE_LOG_MODE_NONE_VAL;
    }

    public String getLOGBOOK_SETTINGS_TEMPLATE_LOG_MODE_COPY_VAL() {
        return LOGBOOK_SETTINGS_TEMPLATE_LOG_MODE_COPY_VAL;
    }

    public String getLOGBOOK_SETTINGS_TEMPLATE_LOG_MODE_TEMPLATE_VAL() {
        return LOGBOOK_SETTINGS_TEMPLATE_LOG_MODE_TEMPLATE_VAL;
    }

    @Override
    public String getItemElementsListTitle() {
        return "Log Document Sections";
    }

    private PropertyValue getLogbookSettingsProperty() {
        ItemDomainLogbook current = getCurrent();

        return getLogbookSettingsProperty(current);

    }

    private PropertyValue getLogbookSettingsProperty(ItemDomainLogbook logbookItem) {
        return logbookItem.getLogbookDocumentSettings();
    }

    private PropertyValue getOrCreateLogbookSettingsProperty() {
        PropertyValue logbookSettingsProperty = getLogbookSettingsProperty();

        if (logbookSettingsProperty == null) {
            try {
                String LOGBOOK_SETTINGS_PROPERTY_TYPE_NAME = ItemDomainLogbook.LOGBOOK_SETTINGS_PROPERTY_TYPE_NAME;
                return addSystemPropertyValue(LOGBOOK_SETTINGS_PROPERTY_TYPE_NAME, true, "");
            } catch (CdbException ex) {
                SessionUtility.addErrorMessage("ERROR", ex.getErrorMessage());
            }
        }
        return logbookSettingsProperty;
    }

    private void setLogbookSettingPropertyKey(String key, String value) {
        PropertyValue logbookSettingsProperty = getOrCreateLogbookSettingsProperty();

        if (logbookSettingsProperty == null) {
            SessionUtility.addErrorMessage("ERROR", "Cannot update setting no setting property value exists.");
            return;
        }

        logbookSettingsProperty.setPropertyMetadataValue(key, value);
    }

    private boolean getLogbookSettingBoolean(boolean defaultValue, String settingKey) {
        String logbookSetting = getLogbookSetting(null, settingKey);

        if (logbookSetting != null) {
            return Boolean.parseBoolean(logbookSetting);
        }

        return defaultValue;
    }

    private String getLogbookSetting(String defaultValue, String settingKey) {
        PropertyValue logbookSettingsProperty = getLogbookSettingsProperty();

        if (logbookSettingsProperty != null) {
            String propertyMetadataValueForKey = logbookSettingsProperty.getPropertyMetadataValueForKey(settingKey);
            if (propertyMetadataValueForKey != null) {
                return propertyMetadataValueForKey;
            }
        }

        return defaultValue;
    }

    private void displayMessageAndRefreshCurrent(String summary, String message) {
        SessionUtility.addErrorMessage(summary, message);

        try {
            String domainPath = getDomainPath();
            String viewForCurrentEntity = viewForCurrentEntity();
            String url = String.format("%s/%s", domainPath, viewForCurrentEntity);
            SessionUtility.redirectTo(url);
        } catch (IOException ex) {
            SessionUtility.addErrorMessage("Error", ex.getMessage());
            logger.error(ex);
        }
    }

    private boolean isSaveLogLockoutsForCurrent() {
        return isSaveLogLockoutsForCurrent(null);
    }

    private boolean isSaveLogLockoutsForCurrent(Log log) {
        // Use current for the lockout timeout especially for documents with sections. 
        ItemDomainLogbook current = getCurrent();
        EntityInfo entityInfo = current.getEntityInfo();
        boolean isEntityWriteableByTimeout = entityInfo.refreshWriteableByTimeout();

        if (isEntityWriteableByTimeout == false) {
            displayMessageAndRefreshCurrent("Cannot change log entries", "Log document is locked by lockout time.");
            setNewLogEdit(null);
            return false;
        }

        if (log != null) {
            Double logLockoutHours = current.getLogLockoutHours();
            Date lastModifiedOnDateTime = log.getLastModifiedOnDateTime();

            boolean isWriteable = AuthorizationUtility.isEntityWriteableByTimeout(logLockoutHours, lastModifiedOnDateTime);
            if (!isWriteable) {
                displayMessageAndRefreshCurrent("Cannot change log entry", "Log entry is locked by lockout time.");
                setNewLogEdit(null);
                return isWriteable;
            }
        }

        return true;
    }

    @Override
    public Log prepareAddLog(ItemDomainLogbook cdbDomainEntity) {
        if (!isSaveLogLockoutsForCurrent()) {
            return null;
        }

        String logbookTemplateLogMode = getLogbookTemplateLogMode();

        Log log = super.prepareAddLog(cdbDomainEntity);

        if (logbookTemplateLogMode.equals(LOGBOOK_SETTINGS_TEMPLATE_LOG_MODE_TEMPLATE_VAL)) {
            Item createdFromTemplate = cdbDomainEntity.getCreatedFromTemplate();
            if (createdFromTemplate != null) {
                List<Log> logList = createdFromTemplate.getLogList();
                if (logList.size() > 0) {
                    Log templateLog = logList.get(0);
                    String templateText = templateLog.getText();
                    log.setText(templateText);
                }

            }
        }

        return log;
    }

    public void prepareCreateLogbookSection() {

        UserInfo user = SessionUtility.getUser();
        ItemDomainLogbook createEntityInstance = getControllerUtility().createEntityInstance(user);

        if (isCurrentItemTemplate()) {
            try {
                appendTemplateEntityType(createEntityInstance);
            } catch (CdbException ex) {
                return;
            }
        }

        getCurrent().setNewLogbookSection(createEntityInstance);
    }

    public String createLogbookSection() {
        ItemDomainLogbook current = getCurrent();
        ItemDomainLogbookControllerUtility controllerUtility = getControllerUtility();

        UserInfo user = SessionUtility.getUser();
        ItemElement newElement = controllerUtility.createItemElement(current, user);
        controllerUtility.prepareAddItemElement(current, newElement);

        ItemDomainLogbook newLogbookSection = current.getNewLogbookSection();
        // Ensure unique names per parent. 
        newLogbookSection.setItemIdentifier2("" + current.getId());

        newElement.setContainedItem(newLogbookSection);

        // Save 
        try {
            controllerUtility.update(current, user);

        } catch (Exception ex) {
            String persitanceErrorMessage = current.getPersitanceErrorMessage();
            SessionUtility.addErrorMessage("Error", persitanceErrorMessage);

            // Reload Current to try again. 
            reloadCurrent();
            current = getCurrent();
            current.setNewLogbookSection(newLogbookSection);
            return null;
        }

        return viewForCurrentEntity();
    }

    @Override
    protected void additionalSelectionOfTemplateSteps() {
        ItemDomainLogbook current = getCurrent();

        Boolean copyLogs = false;
        PropertyValue logbookSettingsProperty = getLogbookSettingsProperty(current);

        if (logbookSettingsProperty != null) {
            String logMode = logbookSettingsProperty.getPropertyMetadataValueForKey(LOGBOOK_SETTINGS_TEMPLATE_LOG_MODE_KEY);
            if (logMode != null) {
                copyLogs = logMode.equals(LOGBOOK_SETTINGS_TEMPLATE_LOG_MODE_COPY_VAL);
            }
        }

        ItemDomainLogbook originalTemplateToCreateNewItem = getTemplateToCreateNewItem();

        if (copyLogs) {
            copyLogs(originalTemplateToCreateNewItem, current);
        }

        UserInfo user = SessionUtility.getUser();

        // Ensure sort order is set. 
        List<ItemElement> templateElements = templateToCreateNewItem.getItemElementDisplayList();
        Float sortOrder = 0.0f;
        for (ItemElement templateElement : templateElements) {
            Float elementSortOrder = templateElement.getSortOrder();
            if (elementSortOrder != null) {
                sortOrder = elementSortOrder;
            }

            templateElement.setSortOrder(sortOrder);
            sortOrder += 1;
        }

        getControllerUtility().cloneCreateItemElements(current, templateToCreateNewItem, user, true, true, true);

        List<ItemElement> itemElementDisplayList = current.getItemElementDisplayList();
        for (ItemElement ie : itemElementDisplayList) {
            ItemDomainLogbook containedItem = (ItemDomainLogbook) ie.getContainedItem();
            ItemDomainLogbook newItem = null;

            try {
                newItem = (ItemDomainLogbook) containedItem.clone(user, user.getUserGroupList().get(0), false, false, false);
            } catch (CloneNotSupportedException ex) {
                SessionUtility.addErrorMessage("Error", ex.getMessage());
            }

            newItem.getEntityTypeList().clear();
            newItem.setName(containedItem.getName());
            newItem.setItemIdentifier2(current.getViewUUID());

            setTemplateToCreateNewItem(containedItem);
            setCurrent(newItem);

            if (copyLogs) {
                copyLogs(containedItem, newItem);
            }

            completeSelectionOfTemplate();

            ie.setContainedItem(newItem);
        }

        setTemplateToCreateNewItem(originalTemplateToCreateNewItem);
        setCurrent(current);

        super.additionalSelectionOfTemplateSteps();
    }

    public void prepareEditLogEntry(Log entry) {
        if (isSaveLogLockoutsForCurrent(entry)) {
            setNewLogEdit(entry);
        }
    }

    private void updateModifiedDateForCurrent() {
        ItemDomainLogbook current = getCurrent();
        EntityInfo entityInfo = current.getEntityInfo();
        UserInfo user = SessionUtility.getUser();
        EntityInfoUtility.updateEntityInfo(entityInfo, user);
        EntityInfoControllerUtility eicu = getEntityInfoControllerUtility();
        try {
            eicu.update(entityInfo, user);
        } catch (CdbException ex) {
            logger.error(ex);
            SessionUtility.addErrorMessage("Error saving modified information", ex.getMessage());
        } catch (RuntimeException ex) {
            logger.error(ex);
            SessionUtility.addErrorMessage("Error saving modified information", ex.getMessage());
        }
    }

    public void destroyLogEntry(Log entry) {
        if (isSaveLogLockoutsForCurrent(entry)) {
            LogController instance = LogController.getInstance();
            instance.destroy(entry);
        }

        updateModifiedDateForCurrent();
    }

    @Override
    public String saveLogList() {
        lastLog = newLogEdit; 
        if (newLogEdit.getId() == null) {
            List<ItemElement> itemElementList = newLogEdit.getItemElementList();
            ItemDomainLogbook parentItem = (ItemDomainLogbook) itemElementList.get(0).getParentItem();
            newLogEdit = null;
            
            parentItem = (ItemDomainLogbook) getItem(parentItem.getId());
            List<Log> logList = parentItem.getLogList();
            lastLog = logList.get(logList.size() - 1);
        }

        updateModifiedDateForCurrent();

        return viewForCurrentEntity();
    }

    @Override
    public String update() {
        // Refresh logs from DB before update. 
        ItemDomainLogbook current = getCurrent();
        Integer id = current.getId();
        ItemDomainLogbook findById = findById(id);
        List<Log> latestLogs = findById.getLogList();
        current.setLogList(latestLogs);

        return super.update();
    }

    public Log getLastLog() {
        if (lastLog != null) {
            Log temp = lastLog;
            lastLog = null;
            return temp;
        }
        return lastLog;
    }

    @Override
    public void processViewRequestParams() {
        super.processViewRequestParams();

        String logId = SessionUtility.getRequestParameterValue("logId");

        if (logId != null) {
            int logIdInt = Integer.parseInt(logId);
            Log log = logFacade.find(logIdInt);
            lastLog = log;
        }
    }

    public void processPreRenderOPSList() {
        if (currentEntityType != null) {
            String name = currentEntityType.getName();
            if (name.equals(OPS_ENTITY_TYPE_NAME)) {
                return;
            }
        }

        EntityType opsET = entityTypeFacade.findByName(OPS_ENTITY_TYPE_NAME);
        redirectToEntityTypeList(opsET);
    }

    private void redirectToEntityTypeList(EntityType entityType) {
        // Prevent redirect to a parent entity type. 
        List<EntityType> entityTypeChildren = entityType.getEntityTypeChildren();
        if (!entityTypeChildren.isEmpty()) {
            EntityType childET = entityTypeChildren.get(0);
            SessionUtility.addWarningMessage("Cannot load parent type.", "Redirecting to first child of type.");
            redirectToEntityTypeList(childET);
            return;
        }

        currentEntityType = entityType;
        ItemDomainLogbookLazyDataModel itemLazyDataModel = getItemLazyDataModel();
        String entityTypeName = entityType.getName();
        itemLazyDataModel.setCurrentEntityType(entityTypeName);

        String redirect = getListRedirectForEntityType(entityType, false);
        try {
            SessionUtility.redirectTo(redirect);
        } catch (IOException ex) {
            logger.error(ex);
            SessionUtility.addErrorMessage("Error", ex.getMessage());
        }
    }

    private String getListRedirectForEntityType(EntityType entityType, boolean includeETURLParam) {
        String listUrl = entityType.getCustomListUrl();
        if (listUrl == null) {
            listUrl = "list";
            if (includeETURLParam) {
                listUrl += String.format("?et=%d", entityType.getId());
            }
        }

        String redirect = String.format("%s/%s", getDomainPath(), listUrl);

        return redirect;

    }

    @Override
    public void processPreRenderList() {
        super.processPreRenderList();

        EntityType lastEntityType = currentEntityType;
        String currentEntityTypeIdStr = SessionUtility.getRequestParameterValue("et");

        if (currentEntityTypeIdStr != null) {
            int etId = Integer.parseInt(currentEntityTypeIdStr);
            EntityType et = entityTypeFacade.find(etId);
            redirectToEntityTypeList(et);
        }

        if (currentEntityType == null) {
            if (lastEntityType != null) {
                currentEntityType = lastEntityType;
            } else {
                List<EntityType> topLevelEntityTypeList = getTopLevelEntityTypeList();
                SessionUtility.addWarningMessage("No list selected", "Redirecting to first list.");
                EntityType et = topLevelEntityTypeList.get(0);
                redirectToEntityTypeList(et);
            }
        }

    }

    @Override
    public void processPreRenderTemplateList() {
        super.processPreRenderList();
    }

    @Override
    public ItemDomainLogbook createEntityInstance() {
        ItemDomainLogbook entity = super.createEntityInstance();

        if (currentEntityType != null) {
            try {
                entity.setEntityTypeList(new ArrayList<>());
                EntityType entityType = currentEntityType;
                entity.getEntityTypeList().add(entityType);

                Item primaryTemplateItem = entityType.getPrimaryTemplateItem();
                if (primaryTemplateItem != null) {
                    templateToCreateNewItem = (ItemDomainLogbook) primaryTemplateItem;
                    completeSelectionOfTemplate();
                }
            } catch (CdbException ex) {
                logger.error(ex);
            }
        }

        return entity;
    }

    @Override
    protected void appendTemplateEntityType(ItemDomainLogbook item) throws CdbException {
        List<EntityType> entityTypeList = item.getEntityTypeList();
        if (entityTypeList != null) {
            entityTypeList.clear();
        }
        super.appendTemplateEntityType(item);
    }

    @Override
    protected void performDestroyOperation(ItemDomainLogbook entity) throws CdbException {
        if (entity.getIsItemTemplate()) {
            List<Item> itemsCreatedFromThisTemplateItem = entity.getItemsCreatedFromThisTemplateItem();

            if (itemsCreatedFromThisTemplateItem.size() > 0) {
                throw new CdbException("The item has template instances.");
            }
        }

        ItemDomainLogbookControllerUtility controllerUtility = getControllerUtility();
        UserInfo user = SessionUtility.getUser();

        List<ItemDomainLogbook> itemsToDestroy = new ArrayList<>();

        for (ItemElement child : entity.getItemElementDisplayList()) {
            ItemDomainLogbook containedItem = (ItemDomainLogbook) child.getContainedItem();
            itemsToDestroy.add(containedItem);
        }

        controllerUtility.destroy(entity, user);
        controllerUtility.destroyList(itemsToDestroy, null, user);
    }

    @Override
// TODO this may not be needed once the property gets its own custom UI. 
    public String updateEditProperty() {
        super.updateEditProperty();
        return viewForCurrentEntity();
    }

    @Override
    public void destroy(ItemDomainLogbook entity) {
        super.destroy(entity); // Generated from nbfs://nbhost/SystemFileSystem/Templates/Classes/Code/OverriddenMethodBody
    }

    @Override
    public String destroy() {
        return super.destroy(); // Generated from nbfs://nbhost/SystemFileSystem/Templates/Classes/Code/OverriddenMethodBody
    }

    @Override
    public boolean isDisplayRowExpansionAssembly(Item item) {
        return false;
    }

    @Override
    public String getItemListPageTitle() {
        String itemListPageTitle = super.getItemListPageTitle();

        if (currentEntityType != null) {
            String displayName = currentEntityType.getLongDisplayName();;

            if (displayName == null || displayName.isBlank()) {
                displayName = currentEntityType.getDisplayName();
            }

            itemListPageTitle = displayName + " " + itemListPageTitle;
        }
        return itemListPageTitle;
    }

    public void navigateToLogDocumentList() {
        EntityType entityType = getCurrent().getEntityTypeList().get(0);

        redirectToEntityTypeList(entityType);
    }

    public ItemDomainLogbook getNextLogDocument() {
        ItemDomainLogbook nextDoc;
        ItemDomainLogbook currentDoc = getCurrent();
        boolean nextDocLoaded = currentDoc.getNextDocLoaded();
        if (!nextDocLoaded) {
            Integer logId = currentDoc.getId();
            String entityTypeName = currentDoc.getEntityTypeList().get(0).getName();
            nextDoc = itemDomainLogbookFacade.getNextLogDocument(entityTypeName, logId);
            currentDoc.setNextDoc(nextDoc);
            currentDoc.setNextDocLoaded(true);
        } else {
            nextDoc = currentDoc.getNextDoc();
        }
        return nextDoc;
    }

    public ItemDomainLogbook getPrevLogDocument() {
        ItemDomainLogbook prevDoc;
        ItemDomainLogbook currentDoc = getCurrent();
        boolean prevDocLoaded = currentDoc.getPrevDocLoaded();
        if (!prevDocLoaded) {
            Integer logId = currentDoc.getId();
            String entityTypeName = currentDoc.getEntityTypeList().get(0).getName();
            prevDoc = itemDomainLogbookFacade.getPreviousLogDocument(entityTypeName, logId);
            currentDoc.setPrevDoc(prevDoc);
            currentDoc.setPrevDocLoaded(true);
        } else {
            prevDoc = currentDoc.getPrevDoc();
        }
        return prevDoc;
    }

    public String navigateToNextDoc() {
        String nextId = getNextLogDocument().getId().toString();
        return "view?id=" + nextId + "&faces-redirect=true";
    }

    public Boolean getNextPageButtonDisabled() {
        ItemDomainLogbook nextDoc = getNextLogDocument();
        return nextDoc == null;
    }

    public String navigateToPrevDoc() {
        String prevId = getPrevLogDocument().getId().toString();
        return "view?id=" + prevId + "&faces-redirect=true";
    }

    public Boolean getPrevPageButtonDisabled() {
        ItemDomainLogbook prevDoc = getPrevLogDocument();
        return prevDoc == null;
    }

    @Override
    public void performEntitySearch(String searchString, boolean caseInsensitive) {
        super.performEntitySearch(searchString, caseInsensitive);

        // Search log entries. 
        List<Object[]> results = itemDomainLogbookFacade.searchEntityLogs(searchString);

        ItemDomainLogbookControllerUtility controllerUtility1 = getControllerUtility();
        String patternString = controllerUtility1.generatePatternString(searchString);
        Pattern searchPattern = controllerUtility1.getSearchPattern(patternString, caseInsensitive);

        logResults = new ArrayList<>();

        for (Object[] result : results) {
            ItemDomainLogbook logbook = (ItemDomainLogbook) result[0];
            Log log = (Log) result[1];
            Long logId = (Long) result[2];

            SearchResult searchResult = new SearchResult(logbook, logbook.getId(), logbook.getName());
            searchResult.setAdditionalAttribute("" + logId);

            String text = log.getText();
            String[] logLines = text.split("\n");

            for (int i = 0; i < logLines.length; i++) {
                String lineNum = "log_line_" + (i + 1);
                String lineText = logLines[i];

                searchResult.doesValueContainPattern(lineNum, lineText, searchPattern);
            }
            logResults.add(searchResult);
        }
    }

    public List<SearchResult> getLogResults() {
        return logResults;
    }

    public Item getParentItem(ItemDomainLogbook child) {

        List<Item> parentItemList = getControllerUtility().getParentItemList(child);

        if (parentItemList != null && parentItemList.size() > 0) {
            return parentItemList.get(0);
        }

        return null;
    }

    public String renderExampleMarkdown() {
        return MarkdownParser.getMarkdownExampleHtml();
    }

    public String getExampleMarkdown() {
        return MarkdownParser.getMarkdownExampleText();
    }

    private PropertyType getSystemPropertyType(String propertyTypeName, boolean isInternal) throws CdbException {
        PropertyType propertyType = propertyTypeFacade.findByName(propertyTypeName);

        if (propertyType == null) {
            PropertyTypeControllerUtility propertyTypeUtility = new PropertyTypeControllerUtility();

            propertyType = new PropertyType();
            propertyType.setName(propertyTypeName);
            propertyType.setIsInternal(isInternal);
            propertyType.setAllowedDomainList(new ArrayList<>());
            Domain defaultDomain = getDefaultDomain();
            propertyType.getAllowedDomainList().add(defaultDomain);

            UserInfo user = SessionUtility.getUser();
            propertyType = propertyTypeUtility.create(propertyType, user);
        }

        return propertyType;
    }

    private PropertyValue addSystemPropertyValue(String propertyTypeName, boolean isInternal, String propertyValue) throws CdbException {
        ItemDomainLogbook current = getCurrent();
        PropertyType systemPropertyType = getSystemPropertyType(propertyTypeName, isInternal);

        ItemDomainLogbookControllerUtility utility = getControllerUtility();
        PropertyValue newPropertyValue = utility.preparePropertyTypeValueAdd(current, systemPropertyType);
        newPropertyValue.setValue(propertyValue);

        return newPropertyValue;
    }

    public String updateDefaultForType() {
        List<EntityType> entityTypesToUpdate = new ArrayList();
        ItemDomainLogbook current = getCurrent();
        List<EntityType> primaryTemplateEntityTypeList = current.getPrimaryTemplateEntityTypeList();

        EntityTypeControllerUtility etUtility = new EntityTypeControllerUtility();

        // Generate entity type update list. 
        for (EntityType et : getLogbookEntityTypeList()) {
            EntityType dbEntity = etUtility.findById(et.getId());

            if (primaryTemplateEntityTypeList.contains(et)) {
                Item primaryTemplateItem = dbEntity.getPrimaryTemplateItem();

                if (!current.equals(primaryTemplateItem)) {
                    String message = String.format("Updating entity type '%s' to current item.", et.getName());
                    if (primaryTemplateItem != null) {
                        message = String.format("%s (from previous item %s)", message, primaryTemplateItem.getName());
                    }

                    SessionUtility.addInfoMessage("Updating", message);
                    dbEntity.setPrimaryTemplateItem(current);
                    entityTypesToUpdate.add(dbEntity);
                }
            } else {
                Item primaryTemplateItem = dbEntity.getPrimaryTemplateItem();
                if (current.equals(primaryTemplateItem)) {
                    String message = String.format("Removing %s from %s", et.getName(), current.getName());
                    SessionUtility.addInfoMessage("Clearing", message);

                    dbEntity.setPrimaryTemplateItem(null);
                    entityTypesToUpdate.add(dbEntity);
                }
            }

        }

        if (!entityTypesToUpdate.isEmpty()) {
            UserInfo user = SessionUtility.getUser();

            try {
                etUtility.updateList(entityTypesToUpdate, user);
            } catch (CdbException ex) {
                SessionUtility.addErrorMessage("ERROR", ex.getMessage());
                logger.error(ex);
            } catch (RuntimeException ex) {
                SessionUtility.addErrorMessage("ERROR", ex.getMessage());
                logger.error(ex);
            }
        }

        return viewForCurrentEntity();
    }

    public List<EntityType> getLogbookEntityTypeList() {
        if (logbookEntityTypes == null) {
            List<EntityType> topLevelEntityTypeList = getTopLevelEntityTypeList();
            logbookEntityTypes = new ArrayList<>();

            for (EntityType topLevelEntityType : topLevelEntityTypeList) {
                List<EntityType> entityTypeChildren = topLevelEntityType.getEntityTypeChildren();
                if (entityTypeChildren != null && !entityTypeChildren.isEmpty()) {
                    logbookEntityTypes.addAll(entityTypeChildren);
                } else {
                    logbookEntityTypes.add(topLevelEntityType);
                }
            }
        }
        return logbookEntityTypes;
    }

    public List<ItemDomainLogbook> getRecentCTLDocuments(Integer limit) {
        List<ItemDomainLogbook> findByDomainAndEntityType = itemDomainLogbookFacade.findByDomainAndEntityType(getDefaultDomainName(), "ctl", limit);

        return findByDomainAndEntityType;
    }

    public List<ItemDomainLogbook> getRecentOPSDocuments(Integer limit) {
        List<ItemDomainLogbook> findByDomainAndEntityType = itemDomainLogbookFacade.findByDomainAndEntityType(getDefaultDomainName(), OPS_ENTITY_TYPE_NAME, limit);

        return findByDomainAndEntityType;
    }

    public List<ItemDomainLogbook> getRecentAOPDocuments(Integer limit) {
        List<ItemDomainLogbook> findByDomainAndEntityType = itemDomainLogbookFacade.findByDomainAndEntityType(getDefaultDomainName(), "studies-sr", limit);

        return findByDomainAndEntityType;
    }

    public final String getCurrentListPermalink() {
        if (currentEntityType != null) {
            String redirect = getListRedirectForEntityType(currentEntityType, true);
            String viewPath = String.format("%s%s", contextRootPermanentUrl, redirect);
            return viewPath;
        }
        return null;
    }

    public List<EntityType> getTopLevelEntityTypeList() {
        if (topLevelEntityTypeList == null) {
            topLevelEntityTypeList = entityTypeFacade.findTopLevelByDomain(getDefaultDomain().getId());
        }

        return topLevelEntityTypeList;
    }

    public boolean isActivePage(Integer entityTypeId) {
        if (currentEntityType != null) {
            return Objects.equals(currentEntityType.getId(), entityTypeId);
        }
        return false;
    }

    public boolean isActiveParentPage(Integer parentEntityTypeId) {
        if (currentEntityType != null) {
            EntityType parentEntityType = currentEntityType.getParentEntityType();
            if (parentEntityType != null) {
                return Objects.equals(parentEntityType.getId(), parentEntityTypeId);
            }
        }
        return false;
    }

    // <editor-fold defaultstate="collapsed" desc="Operations functionality.">
    public void prepareCreateOperationsItem(String onSuccess) {
        prepareCreate();

        ItemDomainLogbook current = getCurrent();
        List<ItemDomainLogbook> templatesList = getTemplatesList();

        // Apply template
        for (ItemDomainLogbook template : templatesList) {
            if (template.getName().equals(OPS_TEMPLATE_NAME)) {
                templateToCreateNewItem = template;
                break;
            }
        }
        if (templateToCreateNewItem == null) {
            SessionUtility.addErrorMessage("Cannot proceed", "'" + OPS_TEMPLATE_NAME + "' template must be created before proceeding.");
            return;
        }
        completeSelectionOfTemplate();

        List<ItemDomainLogbook> logbookSections = current.getLogbookSections();

        if (logbookSections.size() != 6) {
            SessionUtility.addErrorMessage("Error", "Template'" + OPS_TEMPLATE_NAME + "' must have 6 sections.");
            return;
        }

        opsSectionCopyList = new ArrayList<>();
        opsSelectedCopyList = new ArrayList<>();
        initialOpsSelectionReset = true;

        for (int i : COPY_OPS_SHIFT_SECTIONS_INX) {
            ItemDomainLogbook section = logbookSections.get(i);

            opsSelectedCopyList.add(section.getName());
            opsSectionCopyList.add(section.getName());
        }

        // Generate shift name 
        generateShiftName(current);

        SessionUtility.executeRemoteCommand(onSuccess);
    }

    private void generateShifTimes(ItemDomainLogbook shiftItem) {
        LocalDateTime now = LocalDateTime.now();

        Integer shiftStart = null;
        Integer shiftEnd = null;

        DayOfWeek dayOfWeek = now.getDayOfWeek();
        Integer hour = now.getHour();

        if (hour < 6 || hour > 21) {
            shiftStart = 23;
            shiftEnd = 7;
            if (dayOfWeek == DayOfWeek.FRIDAY) {
                shiftEnd = 11;
            }
        } else if (hour < 14) {
            shiftStart = 7;
            shiftEnd = 15;
        } else { // if (hour < 22) {            
            shiftStart = 15;
            shiftEnd = 23;
        }

        if (dayOfWeek == DayOfWeek.SATURDAY
                || dayOfWeek == DayOfWeek.SUNDAY) {
            if (hour > 9 && hour < 22) {
                shiftStart = 11;
                shiftEnd = 23;
            } else {
                shiftStart = 23;
                shiftEnd = 11;

                if (dayOfWeek == DayOfWeek.SUNDAY) {
                    shiftEnd = 7;
                }

            }
        }

        LocalDateTime timeStart = now.withHour(shiftStart);
        LocalDateTime timeEnd = now.withHour(shiftEnd);

        if (shiftStart > shiftEnd) {
            timeStart = now;
            timeEnd = null;

            if (hour > 0 && hour < 11) {
                // Shift created on next day
                timeEnd = timeStart;
                timeStart = now.minusHours(24);
            } else {
                timeEnd = timeStart.plusHours(24);
            }

            // Set the start and end dates. 
            timeStart = timeStart.withHour(shiftStart);
            timeEnd = timeEnd.withHour(shiftEnd);
        }

        timeStart = timeStart.withMinute(0);
        timeEnd = timeEnd.withMinute(0);

        shiftItem.setOpsShiftStartTime(timeStart);
        shiftItem.setOpsShiftEndTime(timeEnd);
    }

    private String generateShiftName(ItemDomainLogbook shiftItem) {
        LocalDateTime timeStart = shiftItem.getOpsShiftStartTime();
        if (timeStart == null) {
            generateShifTimes(shiftItem);
            timeStart = shiftItem.getOpsShiftStartTime();
        }
        LocalDateTime timeEnd = shiftItem.getOpsShiftEndTime();

        String dayPart = "";
        String datePart = "";

        int startMonthDay = timeStart.getDayOfMonth();
        int endMonthDay = timeEnd.getDayOfMonth();

        if (startMonthDay != endMonthDay) {

            Month startMonth = timeStart.getMonth();
            Month endMonth = timeEnd.getMonth();

            dayPart = String.format("%s-%s", dayFormatter.format(timeStart), dayFormatter.format(timeEnd));

            if (startMonth == endMonth) {
                datePart = shortDateFormatter.format(timeStart);
                datePart = String.format("%s-%s", datePart, dayYearNumFormatter.format(timeEnd));
            } else {
                // Example: Sunday-Monday, December 31-January 1, 2024 [23:00-07:00] 
                datePart = shortDateFormatter.format(timeStart);
                datePart = String.format("%s-%s", datePart, dateFormatter.format(timeEnd));
            }
        } else {
            dayPart = dayFormatter.format(timeStart);
            datePart = dateFormatter.format(timeStart);
        }

        String shiftStart = timeFormatter.format(timeStart);
        String shiftEnd = timeFormatter.format(timeEnd);

        String shiftName = String.format("%s - %s [%s - %s]", dayPart, datePart, shiftStart, shiftEnd);
        shiftItem.setName(shiftName);
        return shiftName;

    }

    public void regenOpsShiftName() {
        ItemDomainLogbook current = getCurrent();
        generateShiftName(current);
    }

    public String createOperationsItem() {
        List<ItemDomainLogbook> opsLogDocuments = itemDomainLogbookFacade.findByDomainAndEntityTypeAndTopLevel(getDefaultDomainName(), OPS_ENTITY_TYPE_NAME);

        ItemDomainLogbook latestShiftDocument = null;
        for (int i = opsLogDocuments.size() - 1; i >= 0; i--) {
            ItemDomainLogbook logbook = opsLogDocuments.get(i);

            Item createdFromTemplate = logbook.getCreatedFromTemplate();
            if (createdFromTemplate == null) {
                continue;
            }
            if (createdFromTemplate.equals(templateToCreateNewItem)) {
                // Found latest shift log document. 
                latestShiftDocument = logbook;
                break;
            }
        }

        ItemDomainLogbook current = getCurrent();

        if (latestShiftDocument != null) {
            String name = current.getName();
            String latestName = latestShiftDocument.getName();

            if (name.equals(latestName)) {
                SessionUtility.addErrorMessage("Shift Exists", "Cannot create another shift since the current shift already exists.");
                return null;
            }
        }

        EntityInfo entityInfo = current.getEntityInfo();
        UserInfo createdByUser = entityInfo.getCreatedByUser();
        List<ItemDomainLogbook> logbookSections = current.getLogbookSections();
        List<ItemDomainLogbook> lastShiftSections = latestShiftDocument.getLogbookSections();

        // Get first section for personnel and shift type. 
        ItemDomainLogbook sectionOne = logbookSections.get(0);
        String opsPersonnel = current.getOpsPersonnel();
        String opsShiftType = current.getOpsShiftType();
        LocalDateTime opsShiftStartTime = current.getOpsShiftStartTime();
        LocalDateTime opsShiftEndTime = current.getOpsShiftEndTime();
        String shiftStartValue = DateTimeFormatter.ISO_DATE_TIME.format(opsShiftStartTime);
        String shiftEndValue = DateTimeFormatter.ISO_DATE_TIME.format(opsShiftEndTime);

        try {
            // Add properties
            addSystemPropertyValue(OPS_PERSONNEL_PROPERTY_TYPE_NAME, false, opsPersonnel);
            addSystemPropertyValue(OPS_SHIFT_TYPE_PROPERTY_TYPE_NAME, false, opsShiftType);
            addSystemPropertyValue(OPS_SHIFT_START_PROPERTY_TYPE_NAME, false, shiftStartValue);
            addSystemPropertyValue(OPS_SHIFT_END_PROPERTY_TYPE_NAME, false, shiftEndValue);
        } catch (CdbException ex) {
            SessionUtility.addErrorMessage("Error", ex.getErrorMessage());
            return null;
        }

        String sectionOneContents = String.format(OPS_GENERAL_FIRST_LOG_ENTRY, opsPersonnel, opsShiftType);
        sectionOne.addLogEntry(sectionOneContents, createdByUser);

        if (latestShiftDocument != null) {
            // Copy some sections to new shift log.
            for (int sectionIndex = 0; sectionIndex < logbookSections.size(); sectionIndex++) {
                ItemDomainLogbook newSection = logbookSections.get(sectionIndex);
                String name = newSection.getName();

                if (opsSelectedCopyList.contains(name)) {
                    ItemDomainLogbook lastSection = lastShiftSections.get(sectionIndex);
                    copyLogs(lastSection, newSection);
                }
            }
        } else {
            SessionUtility.addInfoMessage("Info", "Created new shift, no previous shift found.");
        }

        return create();
    }

    public List<String> getOpsSectionCopyList() {
        return opsSectionCopyList;
    }

    public List<String> getOpsSelectedCopyList() {
        return opsSelectedCopyList;
    }

    public void setOpsSelectedCopyList(List<String> opsSelectedCopyList) {
        // UI will clear the default list on the initial update of widget. 
        if (opsSelectedCopyList.size() == 0 && initialOpsSelectionReset) {
            initialOpsSelectionReset = false;
            return;
        }
        this.opsSelectedCopyList = opsSelectedCopyList;
    }

    // </editor-fold>
    private void copyLogs(ItemDomainLogbook oldLogDoc, ItemDomainLogbook newLogDoc) {
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

    // <editor-fold defaultstate="collapsed" desc="FacesConverter">
    @FacesConverter(forClass = ItemDomainLogbook.class)
    public static class ItemDomainLogbookControllerConverter implements Converter {

        @Override
        public Object getAsObject(FacesContext facesContext, UIComponent component, String value) {
            try {
                if (value == null || value.length() == 0) {
                    return null;
                }
                ItemDomainLogbookController controller = (ItemDomainLogbookController) facesContext.getApplication().getELResolver().
                        getValue(facesContext.getELContext(), null, controllerNamed);
                return controller.getEntity(getIntegerKey(value));
            } catch (Exception ex) {
                // we cannot get entity from a given key
                logger.warn("Value " + value + " cannot be converted to logbook domain item.");
                return null;
            }
        }

        Integer getIntegerKey(String value) {
            return Integer.valueOf(value);
        }

        String getStringKey(Integer value) {
            StringBuilder sb = new StringBuilder();
            sb.append(value);
            return sb.toString();
        }

        @Override
        public String getAsString(FacesContext facesContext, UIComponent component, Object object) {
            if (object == null) {
                return null;
            }
            if (object instanceof ItemDomainLogbook) {
                ItemDomainLogbook o = (ItemDomainLogbook) object;
                return getStringKey(o.getId());
            } else {
                throw new IllegalArgumentException("object " + object + " is of type " + object.getClass().getName() + "; expected type: " + ItemDomainLogbook.class.getName());
            }
        }

    }
// </editor-fold>
}
