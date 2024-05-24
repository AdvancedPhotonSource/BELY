/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers;

import gov.anl.aps.logr.common.exceptions.CdbException;
import gov.anl.aps.logr.portal.constants.ItemDomainName;
import gov.anl.aps.logr.portal.controllers.settings.EntityTypeSettings;
import gov.anl.aps.logr.portal.controllers.utilities.EntityTypeControllerUtility;
import gov.anl.aps.logr.portal.model.db.beans.DomainFacade;
import gov.anl.aps.logr.portal.model.db.entities.EntityType;
import gov.anl.aps.logr.portal.model.db.beans.EntityTypeFacade;
import gov.anl.aps.logr.portal.model.db.entities.Domain;
import gov.anl.aps.logr.portal.model.db.entities.Item;
import gov.anl.aps.logr.portal.utilities.SessionUtility;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;
import javax.ejb.EJB;
import javax.inject.Named;
import javax.enterprise.context.SessionScoped;
import javax.faces.component.UIComponent;
import javax.faces.context.FacesContext;
import javax.faces.convert.Converter;
import javax.faces.convert.FacesConverter;
import javax.persistence.Cache;
import javax.persistence.EntityManager;
import javax.persistence.EntityManagerFactory;
import javax.persistence.PersistenceContext;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.primefaces.model.DefaultTreeNode;
import org.primefaces.model.TreeNode;

/**
 * Controller that provides functionality to create, edit, delete, and view
 * entity types. 
 * 
 * Entity type is also known as Logbook Type in the case of the logbook domain.  
 */
@Named("entityTypeController")
@SessionScoped
public class EntityTypeController extends CdbEntityController<EntityTypeControllerUtility, EntityType, EntityTypeFacade, EntityTypeSettings> implements Serializable {

    private static final Logger logger = LogManager.getLogger(EntityTypeController.class.getName());

    @EJB
    EntityTypeFacade entityTypeFacade;

    @EJB
    DomainFacade domainFacade;

    @PersistenceContext(unitName = "LogrPortalPU")
    private EntityManager em;

    private TreeNode entityTypeTreeNode = null;
    private TreeNode selectedEntityType = null;

    private List<EntityType> sortableEntityTypeList = null;
    private List<EntityType> parentCandidateEntityTypeList;

    private boolean renderEditDialog = false;
    private boolean renderCreateDialog = false;

    // May be selectable in the future if more domains are added. 
    private final Integer selectedDomainId = ItemDomainName.LOGBOOK_ID;
    private final String selectedDomainName = ItemDomainName.logbook.getValue();

    public static final String CONTROLLER_NAMED = "entityTypeController";

    public static EntityTypeController getInstance() {
        return (EntityTypeController) SessionUtility.findBean(EntityTypeController.CONTROLLER_NAMED);
    }

    @Override
    protected EntityTypeFacade getEntityDbFacade() {
        return entityTypeFacade;
    }

    @Override
    public EntityType findById(Integer id) {
        return entityTypeFacade.find(id);
    }

    public EntityType findByName(String name) {
        return entityTypeFacade.findByName(name);
    }

    private void resetUIVariables() {
        renderCreateDialog = false;
        renderEditDialog = false;
        sortableEntityTypeList = null;
        parentCandidateEntityTypeList = null;
    }

    public void prepareEdit() {
        resetUIVariables();
        renderEditDialog = true;

        parentCandidateEntityTypeList = new ArrayList<>();
        List<EntityType> topLevelEntityTypes = getTopLevelEntityTypes();
        
        EntityType selectedEntityTypeObj = getSelectedEntityTypeObj();

        for (EntityType topLevel : topLevelEntityTypes) {
            if (topLevel.equals(selectedEntityTypeObj)) {
                continue;
            }
            List<Item> itemList = topLevel.getItemList();
            if (itemList.isEmpty()) {
                parentCandidateEntityTypeList.add(topLevel);
            }
        }
    }

    @Override
    public void processPreRenderList() {
        resetUIVariables();

        super.processPreRenderList();
    }

    private List<EntityType> getTopLevelEntityTypes() {
        return entityTypeFacade.findTopLevelByDomain(selectedDomainId);
    }

    public TreeNode getEntityTypeTree() {
        if (entityTypeTreeNode == null) {
            entityTypeTreeNode = new DefaultTreeNode();

            List<EntityType> topLevels = getTopLevelEntityTypes();

            List topLevelNodes = entityTypeTreeNode.getChildren();

            for (EntityType et : topLevels) {
                TreeNode etNode = new DefaultTreeNode(et);
                etNode.setType("parent");
                topLevelNodes.add(etNode);

                List children = etNode.getChildren();
                for (EntityType childEt : et.getEntityTypeChildren()) {
                    TreeNode childNode = new DefaultTreeNode(childEt);
                    childNode.setType("child");
                    children.add(childNode);
                }
            }
        }

        return entityTypeTreeNode;
    }

    public TreeNode getSelectedEntityType() {
        return selectedEntityType;
    }

    public void setSelectedEntityType(TreeNode selectedEntityType) {
        this.selectedEntityType = selectedEntityType;
    }

    public boolean isRenderEditDialog() {
        return renderEditDialog;
    }

    public boolean isRenderCreateDialog() {
        return renderCreateDialog;
    }

    private EntityType getSelectedEntityTypeObj() {
        if (selectedEntityType == null) {
            return null;
        }

        return (EntityType) selectedEntityType.getData();

    }

    @Override
    public void resetListDataModel() {
        super.resetListDataModel();

        entityTypeTreeNode = null;
        selectedEntityType = null;
    }

    public String saveSelectedEntityType() {
        if (selectedEntityType == null) {
            SessionUtility.addErrorMessage("ERROR", "No entity type is selected");
        }

        EntityType selectedEntityTypeObj = getSelectedEntityTypeObj();
        setCurrent(selectedEntityTypeObj);

        update();

        return list();
    }

    public String prepareCreateEntityType() {
        return prepareCreateEntityType(false);
    }

    public String prepareCreateTopLevelEntityType() {
        return prepareCreateEntityType(true);
    }

    private String prepareCreateEntityType(boolean topLevel) {
        EntityType newInstance = createEntityInstance();

        if (!topLevel) {
            EntityType selectedEntityTypeObj = getSelectedEntityTypeObj();
            if (selectedEntityTypeObj == null) {
                SessionUtility.addErrorMessage("ERROR", "No entity type is selected");
                return list();
            }

            if (!selectedEntityTypeObj.getItemList().isEmpty()) {
                SessionUtility.addErrorMessage("Cannot add", "Top level entity type has items of this type.");
                return list();
            }
            newInstance.setParentEntityType(selectedEntityTypeObj);
        }

        List<Domain> allowedDomainList = newInstance.getAllowedDomainList();
        if (allowedDomainList == null) {
            allowedDomainList = new ArrayList<>();
            newInstance.setAllowedDomainList(allowedDomainList);
        }
        Domain selectedDomain = domainFacade.find(selectedDomainId);
        allowedDomainList.add(selectedDomain);

        setCurrent(newInstance);

        resetUIVariables();
        renderCreateDialog = true;

        return null;
    }

    public String createEntityType() {
        create();

        return list();
    }

    public String prepareDestroySelectedEntityType() {
        EntityType selectedEntityTypeObj = getSelectedEntityTypeObj();

        if (selectedEntityTypeObj == null) {
            SessionUtility.addErrorMessage("ERROR", "No selection. Nothing to delete");
            return list();
        }

        EntityType parentEntityType = selectedEntityTypeObj.getParentEntityType();
        if (parentEntityType == null) {
            // Check for children. 
            if (!selectedEntityTypeObj.getEntityTypeChildren().isEmpty()) {
                SessionUtility.addErrorMessage("ERROR", "Cannot proceed, entity type has children.");
                return list();
            }
        }

        // Verify no items exist. 
        List<Item> itemList = selectedEntityTypeObj.getItemList();
        if (!itemList.isEmpty()) {
            SessionUtility.addErrorMessage("ERROR", "Cannot proceed, entity type has items of this type.");
            return list();
        }

        setCurrent(selectedEntityTypeObj);
        return null;
    }

    @Override
    public String destroy() {
        String destroy = super.destroy();
        clearEntityTypeCache();

        return list();
    }

    @Override
    public String create() {
        String create = super.create();
        clearEntityTypeCache();

        return create;
    }

    @Override
    public String update() {
        String update = super.update();
        clearEntityTypeCache();

        return update;
    }

    @Override
    public void updateList(List<EntityType> entities) throws CdbException, RuntimeException {
        super.updateList(entities);

        clearEntityTypeCache();
    }

    public String getListPageTitle() {
        if (selectedDomainId == ItemDomainName.LOGBOOK_ID) {
            return "Logbook Type List";
        }
        return String.format("%s Domain %s List", selectedDomainName, getDisplayEntityTypeName());
    }

    private void clearEntityTypeCache() {
        EntityManagerFactory entityManagerFactory = em.getEntityManagerFactory();
        Cache cache = entityManagerFactory.getCache();
        cache.evict(EntityType.class);
    }

    public String prepareReorderTopLevelEntityTypes() {
        List<EntityType> topLevelEntityTypes = getTopLevelEntityTypes();
        setSortableEntityTypeList(topLevelEntityTypes);

        return null;
    }

    public String prepareReorderEntityTypesForSelection() {
        EntityType selectedEntityTypeObj = getSelectedEntityTypeObj();

        if (selectedEntityTypeObj == null) {
            SessionUtility.addErrorMessage("ERROR", "No selection.");
            return list();
        }

        List<EntityType> children = selectedEntityTypeObj.getEntityTypeChildren();

        if (children == null || children.size() <= 1) {
            SessionUtility.addWarningMessage("Cannot proceed", "Selected entity type has nothing to sort.");
            return list();
        }

        // Load the sort list. 
        List<EntityType> entityTypes = new ArrayList<>();
        entityTypes.addAll(children);
        setSortableEntityTypeList(entityTypes);
        return null;
    }

    public String saveNewSortOrder() {
        if (sortableEntityTypeList != null) {
            float sortOrder = 0;
            for (EntityType et : sortableEntityTypeList) {
                et.setSortOrder(sortOrder);
                sortOrder += 1;
            }
        }

        try {
            updateList(sortableEntityTypeList);
        } catch (CdbException ex) {
            logger.error(ex);
            SessionUtility.addErrorMessage("Error", ex.getMessage());
        } catch (RuntimeException ex) {
            logger.error(ex);
            SessionUtility.addErrorMessage("Error", ex.getMessage());

        }

        return list();
    }

    public List<EntityType> getSortableEntityTypeList() {
        return sortableEntityTypeList;
    }

    public void setSortableEntityTypeList(List<EntityType> sortableEntityTypeList) {
        this.sortableEntityTypeList = sortableEntityTypeList;
    }

    public List<EntityType> getParentCandidateEntityTypeList() {
        return parentCandidateEntityTypeList;
    }

    public void setParentCandidateEntityTypeList(List<EntityType> parentCandidateEntityTypeList) {
        this.parentCandidateEntityTypeList = parentCandidateEntityTypeList;
    }

    @Override
    protected EntityTypeSettings createNewSettingObject() {
        return new EntityTypeSettings();
    }

    @Override
    protected EntityTypeControllerUtility createControllerUtilityInstance() {
        return new EntityTypeControllerUtility();
    }

    @FacesConverter(forClass = EntityType.class, value = "entityTypeConverter")
    public static class EntityTypeControllerConverter implements Converter {

        @Override
        public Object getAsObject(FacesContext facesContext, UIComponent component, String value) {
            if (value == null || value.length() == 0) {
                return null;
            }
            Integer key = getKey(value); 
            if (key == null) {
                return null; 
            }
            
            EntityTypeController controller = (EntityTypeController) facesContext.getApplication().getELResolver().
                    getValue(facesContext.getELContext(), null, "entityTypeController");
            return controller.findById(key);
        }

        java.lang.Integer getKey(String value) {            
            java.lang.Integer key;
            try {
                key = Integer.valueOf(value);
                return key;
            } catch (NumberFormatException ex) {
                return null; 
            }            
        }

        String getStringKey(java.lang.Integer value) {
            StringBuilder sb = new StringBuilder();
            sb.append(value);
            return sb.toString();
        }

        @Override
        public String getAsString(FacesContext facesContext, UIComponent component, Object object) {
            if (object == null) {
                return null;
            }
            if (object instanceof EntityType) {
                EntityType o = (EntityType) object;
                return getStringKey(o.getId());
            } else {
                throw new IllegalArgumentException("object " + object + " is of type " + object.getClass().getName() + "; expected type: " + EntityType.class.getName());
            }
        }

    }

}
