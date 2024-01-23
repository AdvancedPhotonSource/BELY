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
import gov.anl.aps.logr.portal.utilities.MarkdownParser;
import gov.anl.aps.logr.portal.utilities.SearchResult;
import gov.anl.aps.logr.portal.utilities.SessionUtility;
import java.io.IOException;
import java.time.DayOfWeek;
import java.time.LocalDateTime;
import java.time.Month;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
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

    private String currentEntityType = null;
    private Log lastLog;

    private List<SearchResult> logResults;

    private static final String CTL_ENTITY_TYPE_NAME = "ctl";
    private static final String AOP_ENTITY_TYPE_NAME = "aop";
    private static final String OPS_ENTITY_TYPE_NAME = "ops";
    private static final String SANDBOX_ENTITY_TYPE_NAME = "sandbox";

    private static final String LOGBOOK_SETTINGS_PROPERTY_TYPE_NAME = "Logbook Document Settings";
    private static final String LOGBOOK_SETTINGS_SHOW_TIMESTAMP_KEY = "showTimestamps";
    private static final String LOGBOOK_SETTINGS_TEMPLATE_LOG_MODE_KEY = "logMode"; 
    private static final String LOGBOOK_SETTINGS_TEMPLATE_LOG_MODE_NONE_VAL = "none"; 
    private static final String LOGBOOK_SETTINGS_TEMPLATE_LOG_MODE_COPY_VAL = "copy"; 
    private static final String LOGBOOK_SETTINGS_TEMPLATE_LOG_MODE_TEMPLATE_VAL = "template per entry"; 
    private static final String[] LOGBOOK_SETTING_TEMPLATE_LOG_MODES = new String[] {
        LOGBOOK_SETTINGS_TEMPLATE_LOG_MODE_NONE_VAL, 
        LOGBOOK_SETTINGS_TEMPLATE_LOG_MODE_COPY_VAL, 
        LOGBOOK_SETTINGS_TEMPLATE_LOG_MODE_TEMPLATE_VAL
    }; 

    // Custom operations functionality.. 
    // <editor-fold defaultstate="collapsed" desc="Operations specific variables.">
    private static final String OPS_TEMPLATE_NAME = "Operations Shift";
    private static final String OPS_GENERAL_FIRST_LOG_ENTRY = "Personnel: %s \n\n\n Shift Type: %s";                

    private static final DateTimeFormatter dayFormatter = DateTimeFormatter.ofPattern("EEEE");
    private static final DateTimeFormatter dateFormatter = DateTimeFormatter.ofPattern("MMMM dd, yyyy");
    private static final DateTimeFormatter dayYearNumFormatter = DateTimeFormatter.ofPattern("dd, yyyy");
    private static final DateTimeFormatter shortDateFormatter = DateTimeFormatter.ofPattern("MMMM dd");
    private static final DateTimeFormatter timeFormatter = DateTimeFormatter.ofPattern("HH:mm"); 
    
    private static final int[] COPY_OPS_SHIFT_SECTIONS_INX = new int[] {1, 4 ,5}; 
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

    public String[] getLogbookSettingTemplateLogModes() {        
        return LOGBOOK_SETTING_TEMPLATE_LOG_MODES;
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
        PropertyValue logbookDocumentSettings = logbookItem.getLogbookDocumentSettings();

        if (logbookDocumentSettings == null) {
            List<PropertyValue> propertyValueList = logbookItem.getPropertyValueList();

            for (PropertyValue pv : propertyValueList) {
                PropertyType propertyType = pv.getPropertyType();
                String propertyTypeName = propertyType.getName();

                if (propertyTypeName.equals(LOGBOOK_SETTINGS_PROPERTY_TYPE_NAME)) {
                    logbookDocumentSettings = pv;
                    break;
                }
            }

            logbookItem.setLogbookDocumentSettings(logbookDocumentSettings);
        }
        return logbookDocumentSettings;
    }
    
    private PropertyValue getOrCreateLogbookSettingsProperty() {
        PropertyValue logbookSettingsProperty = getLogbookSettingsProperty();
        
        if(logbookSettingsProperty == null) {
            try {
                return addSystemPropertyValue(LOGBOOK_SETTINGS_PROPERTY_TYPE_NAME, "");
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

    @Override
    public Log prepareAddLog(ItemDomainLogbook cdbDomainEntity) {
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
            
            copyLogs = logMode.equals(LOGBOOK_SETTINGS_TEMPLATE_LOG_MODE_COPY_VAL);
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
        setNewLogEdit(entry);
    }

    @Override
    public String saveLogList() {
        List<ItemElement> itemElementList = newLogEdit.getItemElementList();
        ItemDomainLogbook parentItem = (ItemDomainLogbook) itemElementList.get(0).getParentItem();
        newLogEdit = null;

        parentItem = (ItemDomainLogbook) getItem(parentItem.getId());
        List<Log> logList = parentItem.getLogList();
        lastLog = logList.get(logList.size() - 1);

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

    public void processPreRenderCTLList() {
        processPreRenderSpecificList(CTL_ENTITY_TYPE_NAME);
    }

    public void processPreRenderOPSList() {
        processPreRenderSpecificList(OPS_ENTITY_TYPE_NAME);
    }

    public void processPreRenderAOPList() {
        processPreRenderSpecificList(AOP_ENTITY_TYPE_NAME);
    }
    
    public void processPreRenderSandboxList() {
        processPreRenderSpecificList(SANDBOX_ENTITY_TYPE_NAME);
    }

    private void processPreRenderSpecificList(String entityTypeName) {
        super.processPreRenderList();

        currentEntityType = entityTypeName;

        ItemDomainLogbookLazyDataModel itemLazyDataModel = getItemLazyDataModel();
        itemLazyDataModel.setCurrentEntityType(currentEntityType);
    }

    private void redirectToEntityTypeList(String entityType) {
        String redirect = String.format("%s/%sList", getDomainPath(), entityType);
        try {
            SessionUtility.redirectTo(redirect);
        } catch (IOException ex) {
            logger.error(ex);
            SessionUtility.addErrorMessage("Error", ex.getMessage());
        }
    }

    @Override
    public void processPreRenderList() {
        super.processPreRenderList();

        String lastEntityType = currentEntityType;
        currentEntityType = SessionUtility.getRequestParameterValue("logbook");

        if (currentEntityType != null && currentEntityType.equals("none")) {
            ItemDomainLogbookLazyDataModel itemLazyDataModel = getItemLazyDataModel();
            currentEntityType = null;
            itemLazyDataModel.setCurrentEntityType(currentEntityType);
        } else {
            if (currentEntityType == null) {
                if (lastEntityType != null) {
                    currentEntityType = lastEntityType;
                } else {
                    currentEntityType = CTL_ENTITY_TYPE_NAME;
                }
            }
            redirectToEntityTypeList(currentEntityType);
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
                EntityType entityType = entityTypeFacade.findByName(currentEntityType);
                entity.getEntityTypeList().add(entityType);
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
    public String getItemListPageTitle() {
        String itemListPageTitle = super.getItemListPageTitle();

        if (currentEntityType != null) {
            String entityName = null;

            switch (currentEntityType) {
                case CTL_ENTITY_TYPE_NAME:
                    entityName = "Controls";
                    break;
                case OPS_ENTITY_TYPE_NAME:
                    entityName = "Operations";
                    break;
                case SANDBOX_ENTITY_TYPE_NAME:
                    entityName = "Sandbox"; 
                    break;
                default:
                    entityName = currentEntityType.toUpperCase();
                    break;
            }

            itemListPageTitle = entityName + " " + itemListPageTitle;
        }
        return itemListPageTitle;
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
    
    private PropertyType getSystemPropertyType(String propertyTypeName) throws CdbException { 
        PropertyType propertyType = propertyTypeFacade.findByName(propertyTypeName);
        
        if(propertyType == null) {
            PropertyTypeControllerUtility propertyTypeUtility = new PropertyTypeControllerUtility();   
            
            propertyType = new PropertyType(); 
            propertyType.setName(propertyTypeName); 
            propertyType.setAllowedDomainList(new ArrayList<>());
            Domain defaultDomain = getDefaultDomain();
            propertyType.getAllowedDomainList().add(defaultDomain); 
            
            UserInfo user = SessionUtility.getUser();
            propertyType = propertyTypeUtility.create(propertyType, user); 
        }
        
        return propertyType; 
    }
    
    private PropertyValue addSystemPropertyValue(String propertyTypeName, String propertyValue) throws CdbException { 
        ItemDomainLogbook current = getCurrent();
        PropertyType systemPropertyType = getSystemPropertyType(propertyTypeName);
        
        ItemDomainLogbookControllerUtility utility = getControllerUtility();
        PropertyValue newPropertyValue = utility.preparePropertyTypeValueAdd(current, systemPropertyType);                
        newPropertyValue.setValue(propertyValue);                
        
        return newPropertyValue;
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
            SessionUtility.addErrorMessage("Error", "Tempalte '" + OPS_TEMPLATE_NAME + "' must have 6 sections.");
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
                
//        try {
//            // Add properties
//            addSystemPropertyValue(OPS_PERSONNEL_PROPERTY_TYPE_NAME, opsPersonnel);
//            
//        } catch (CdbException ex) {
//            SessionUtility.addErrorMessage("Error", ex.getErrorMessage());
//            return null;
//        }
        
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

        for (Log log : logList) {
            String text = log.getText();
            newLogDoc.addLogEntry(text, createdByUser);

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
