/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.cdb.portal.controllers;

import gov.anl.aps.cdb.common.exceptions.CdbException;
import gov.anl.aps.cdb.portal.constants.EntityTypeName;
import gov.anl.aps.cdb.portal.controllers.extensions.ItemCreateWizardController;
import gov.anl.aps.cdb.portal.controllers.extensions.ItemCreateWizardDomainLogbookController;
import gov.anl.aps.cdb.portal.controllers.settings.ItemDomainLogbookSettings;
import gov.anl.aps.cdb.portal.controllers.utilities.ItemDomainLogbookControllerUtility;
import gov.anl.aps.cdb.portal.model.ItemDomainLogbookLazyDataModel;
import gov.anl.aps.cdb.portal.model.db.beans.ItemDomainLogbookFacade;
import gov.anl.aps.cdb.portal.model.db.beans.LogFacade;
import gov.anl.aps.cdb.portal.model.db.entities.EntityType;
import gov.anl.aps.cdb.portal.model.db.entities.Item;
import gov.anl.aps.cdb.portal.model.db.entities.ItemDomainLogbook;
import gov.anl.aps.cdb.portal.model.db.entities.ItemElement;
import gov.anl.aps.cdb.portal.model.db.entities.Log;
import gov.anl.aps.cdb.portal.model.db.entities.UserInfo;
import gov.anl.aps.cdb.portal.utilities.SearchResult;
import gov.anl.aps.cdb.portal.utilities.SessionUtility;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.regex.Pattern;
import javax.ejb.EJB;
import javax.enterprise.context.SessionScoped;
import javax.faces.model.DataModel;
import javax.faces.model.ListDataModel;
import javax.inject.Named;

/**
 *
 * @author djarosz
 */
@Named(ItemDomainLogbookController.controllerNamed)
@SessionScoped
public class ItemDomainLogbookController extends ItemController<ItemDomainLogbookControllerUtility, ItemDomainLogbook, ItemDomainLogbookFacade, ItemDomainLogbookSettings, ItemDomainLogbookLazyDataModel> {

    @EJB
    ItemDomainLogbookFacade itemDomainLogbookFacade;
    
    @EJB
    LogFacade logFacade; 

    private String currentEntityType = null;
    private Log lastLog; 
    
    private List<SearchResult> logResults; 

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
    public DataModel getTemplateItemsListDataModel() {
        if (templateItemsListDataModel == null) {
            List<ItemDomainLogbook> templates = getEntityDbFacade().findByDomainAndEntityTypeAndTopLevel(getDefaultDomainName(), EntityTypeName.template.getValue());
            templateItemsListDataModel = new ListDataModel(templates);
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

    @Override
    public String getItemElementsListTitle() {
        return "Logbook Sections";
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
    public void completeSelectionOfTemplate() {
        ItemDomainLogbook current = getCurrent();

        if (this.templateToCreateNewItem != null) {
            ItemDomainLogbook originalTemplateToCreateNewItem = getTemplateToCreateNewItem();

            UserInfo user = SessionUtility.getUser();
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

                completeSelectionOfTemplate();

                ie.setContainedItem(newItem);
            }

            setTemplateToCreateNewItem(originalTemplateToCreateNewItem);
            setCurrent(current);

        }
        super.completeSelectionOfTemplate();
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

    @Override
    public void processPreRenderList() {
        super.processPreRenderList();

        ItemDomainLogbookLazyDataModel itemLazyDataModel = getItemLazyDataModel();
        String lastEntityType = currentEntityType; 
        currentEntityType = SessionUtility.getRequestParameterValue("logbook");
        
        if (currentEntityType == null) {
            if (lastEntityType != null) {
                currentEntityType = lastEntityType; 
            } else {
                currentEntityType = "ctl"; 
            }            
        } else if (currentEntityType.equals("none")) { 
            currentEntityType = null; 
        }
        
        itemLazyDataModel.setCurrentEntityType(currentEntityType);
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
                Logger.getLogger(ItemDomainLogbookController.class.getName()).log(Level.SEVERE, null, ex);
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

//    @Override
//    protected void performDestroyOperation(ItemDomainLogbook entity) throws CdbException {
//        ItemDomainLogbookControllerUtility controllerUtility = getControllerUtility();
//        UserInfo user = SessionUtility.getUser();
//        
//        List<ItemDomainLogbook> itemsToDestroy = new ArrayList<>();        
//        
//        for (ItemElement child : entity.getItemElementDisplayList()) {
//            ItemDomainLogbook containedItem = (ItemDomainLogbook) child.getContainedItem();
//            itemsToDestroy.add(containedItem);           
//        }
//        
//        
//        controllerUtility.destroy(entity, user);
//        controllerUtility.destroyList(itemsToDestroy, null, user);  
//
//
//    }

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
            itemListPageTitle = currentEntityType.toUpperCase() + " " + itemListPageTitle; 
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
                String lineNum = "log_line_" + (i+1); 
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


}
