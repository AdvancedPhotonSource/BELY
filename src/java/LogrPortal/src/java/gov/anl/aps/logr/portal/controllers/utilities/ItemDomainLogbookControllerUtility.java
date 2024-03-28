/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.utilities;

import gov.anl.aps.logr.portal.constants.ItemDomainName;
import gov.anl.aps.logr.portal.model.db.beans.ItemDomainLogbookFacade;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook;
import gov.anl.aps.logr.portal.model.db.entities.ItemElement;
import gov.anl.aps.logr.portal.model.db.entities.Log;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
import java.util.ArrayList;
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

    @Override
    public Log prepareAddLog(ItemDomainLogbook cdbDomainEntity, UserInfo user) {
        Log log = super.prepareAddLog(cdbDomainEntity, user); 
        
        log.setItemElementList(new ArrayList<>());
        ItemElement selfElement = cdbDomainEntity.getSelfElement();
        
        log.getItemElementList().add(selfElement);         
        
        return log; 
    }
    
    public Map createAdvancedSearchMap(String entityTypeIdList, String itemTypeIdList, Date startTime, Date endTime) {
        /**
         * Generates the searchOpts for the searchEntities functionality. Can also be used with CdbEntityController.performEntitySearch(); 
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
         * search opts include the following keys:
         *   - entity_type_id (logbook type id)
         *   - item_type_id (system id)
         *   - start_time (start modified date search criteria)
         *   - end_time (end modified date search criteria) 
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
   
}
