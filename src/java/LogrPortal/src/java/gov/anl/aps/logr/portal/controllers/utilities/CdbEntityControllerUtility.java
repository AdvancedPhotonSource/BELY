/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.utilities;

import com.fasterxml.jackson.core.JsonProcessingException;
import fish.payara.cloud.connectors.mqtt.api.MQTTConnection;
import fish.payara.cloud.connectors.mqtt.api.MQTTConnectionFactory;
import gov.anl.aps.logr.common.exceptions.CdbException;
import gov.anl.aps.logr.common.mqtt.model.AddEvent;
import gov.anl.aps.logr.common.mqtt.model.DeleteEvent;
import gov.anl.aps.logr.common.mqtt.model.UpdateEvent;
import gov.anl.aps.logr.common.mqtt.model.MqttEvent;
import gov.anl.aps.logr.common.utilities.StringUtility;
import gov.anl.aps.logr.portal.constants.SystemLogLevel;
import gov.anl.aps.logr.portal.model.db.beans.CdbEntityFacade;
import gov.anl.aps.logr.portal.model.db.entities.CdbEntity;
import gov.anl.aps.logr.portal.model.db.entities.PropertyType;
import gov.anl.aps.logr.portal.model.db.entities.PropertyValue;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
import gov.anl.aps.logr.portal.utilities.SearchResult;
import gov.anl.aps.logr.portal.utilities.SessionUtility;
import java.util.Date;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.regex.Pattern;
import org.apache.commons.lang3.exception.ExceptionUtils;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

/**
 * Controller utility provides unified functionality for managing entities to be
 * used from view controllers as well as API endpoints.
 *
 * @author darek
 * @param <EntityType> Database mapped class of the entity.
 * @param <FacadeType> Database facade provides communication to database.
 */
public abstract class CdbEntityControllerUtility<EntityType extends CdbEntity, FacadeType extends CdbEntityFacade<EntityType>> {

    private static final Logger logger = LogManager.getLogger(CdbEntityControllerUtility.class.getName());

    protected void publishMqttEvent(MqttEvent event) {
        MQTTConnectionFactory mqttFactory = SessionUtility.fetchMQTTConnectionFactory();
        String jsonMessage;

        try {
            jsonMessage = event.toJson();
        } catch (JsonProcessingException ex) {
            logger.error(ex);
            return;
        }

        if (mqttFactory == null) {
            logger.warn("MQTT not configured. Skipping event: " + jsonMessage);
            return;
        }
        MQTTConnection connection = mqttFactory.getConnection();
        try {
            connection.publish(event.getTopic().getValue(), jsonMessage.getBytes(), 0, false);
        } catch (Exception ex) {
        }
    }

    /**
     * Abstract method for returning entity DB facade.
     *
     * @return entity DB facade
     */
    protected abstract FacadeType getEntityDbFacade();

    /**
     * Abstract method for creating new entity instance.
     *
     * @return created entity instance
     */
    public abstract EntityType createEntityInstance(UserInfo sessionUser);

    public EntityType create(EntityType entity, UserInfo createdByUserInfo) throws CdbException, RuntimeException {
        try {
            prepareEntityInsert(entity, createdByUserInfo);
            getEntityDbFacade().create(entity);

            addCreatedSystemLog(entity, createdByUserInfo);
            entity.setPersitanceErrorMessage(null);
            publishMqttEvent(new AddEvent(entity, "Add action completed"));

            clearCaches();
            return entity;
        } catch (CdbException ex) {
            logger.error("Could not create " + getDisplayEntityTypeName() + ": " + ex.getMessage());
            addCreatedWarningSystemLog(ex, entity, createdByUserInfo);
            entity.setPersitanceErrorMessage(ex.getMessage());
            throw ex;
        } catch (RuntimeException ex) {
            Throwable t = ExceptionUtils.getRootCause(ex);
            logger.error("Could not create " + getDisplayEntityTypeName() + ": " + t.getMessage());
            addCreatedWarningSystemLog(ex, entity, createdByUserInfo);
            entity.setPersitanceErrorMessage(ex.getMessage());
            throw ex;
        }
    }

    public void createList(List<EntityType> entities, UserInfo createdByUserInfo) throws CdbException, RuntimeException {
        try {
            for (EntityType entity : entities) {
                prepareEntityInsert(entity, createdByUserInfo);
            }
            getEntityDbFacade().create(entities);

            addCdbEntitySystemLog(SystemLogLevel.entityInfo, "Created " + entities.size() + " entities.", createdByUserInfo);
            for (EntityType entity : entities) {
                publishMqttEvent(new AddEvent(entity, "Add action completed"));
            }
            setPersistenceErrorMessageForList(entities, null);
            clearCaches();
        } catch (CdbException ex) {
            logger.error("Could not create " + getDisplayEntityTypeName() + ": " + ex.getMessage());
            setPersistenceErrorMessageForList(entities, ex.getMessage());
            addCdbEntityWarningSystemLog("Failed to create list of entities: " + getDisplayEntityTypeName(), ex, null, createdByUserInfo);
            throw ex;
        } catch (RuntimeException ex) {
            Throwable t = ExceptionUtils.getRootCause(ex);
            logger.error("Could not create list of " + getDisplayEntityTypeName() + ": " + t.getMessage());
            setPersistenceErrorMessageForList(entities, ex.getMessage());
            addCdbEntityWarningSystemLog("Failed to create list of entities: " + getDisplayEntityTypeName(), ex, null, createdByUserInfo);
            throw ex;
        }
    }

    public EntityType update(EntityType entity, UserInfo updatedByUserInfo) throws CdbException, RuntimeException {
        try {
            logger.debug("Updating " + getDisplayEntityTypeName() + " " + getEntityInstanceName(entity));
            prepareEntityUpdate(entity, updatedByUserInfo);
            EntityType updatedEntity = getEntityDbFacade().edit(entity);
            addCdbEntitySystemLog(SystemLogLevel.entityInfo, "Updated: " + entity.getSystemLogString(), updatedByUserInfo);
            publishMqttEvent(new UpdateEvent(entity, "Update action completed"));
            entity.setPersitanceErrorMessage(null);

            clearCaches();
            return updatedEntity;
        } catch (CdbException ex) {
            entity.setPersitanceErrorMessage(ex.getMessage());
            addCdbEntityWarningSystemLog("Failed to update", ex, entity, updatedByUserInfo);
            logger.error("Could not update " + getDisplayEntityTypeName() + " "
                    + getEntityInstanceName(entity) + ": " + ex.getMessage());
            throw ex;
        } catch (RuntimeException ex) {
            Throwable t = ExceptionUtils.getRootCause(ex);
            logger.error("Could not update " + getDisplayEntityTypeName() + " "
                    + getEntityInstanceName(entity) + ": " + t.getMessage());
            addCdbEntityWarningSystemLog("Failed to update", ex, entity, updatedByUserInfo);
            entity.setPersitanceErrorMessage(t.getMessage());
            throw ex;
        }
    }

    public EntityType updateOnRemoval(EntityType entity, UserInfo updatedByUserInfo) throws CdbException, RuntimeException {
        try {
            logger.debug("Updating " + getDisplayEntityTypeName() + " " + getEntityInstanceName(entity));
            prepareEntityUpdateOnRemoval(entity);
            EntityType updatedEntity = getEntityDbFacade().edit(entity);
            clearCaches();

            publishMqttEvent(new UpdateEvent(entity, "Update on removal action completed"));

            return updatedEntity;
        } catch (CdbException ex) {
            entity.setPersitanceErrorMessage(ex.getMessage());
            addCdbEntityWarningSystemLog("Failed to update", ex, entity, updatedByUserInfo);
            logger.error("Could not update " + getDisplayEntityTypeName() + " "
                    + getEntityInstanceName(entity) + ": " + ex.getMessage());
            throw ex;
        } catch (RuntimeException ex) {
            Throwable t = ExceptionUtils.getRootCause(ex);
            logger.error("Could not update " + getDisplayEntityTypeName() + " "
                    + getEntityInstanceName(entity) + ": " + t.getMessage());
            addCdbEntityWarningSystemLog("Failed to update", ex, entity, updatedByUserInfo);
            entity.setPersitanceErrorMessage(t.getMessage());
            throw ex;
        }
    }

    public void updateList(List<EntityType> entities, UserInfo updatedByUserInfo) throws CdbException, RuntimeException {
        try {
            for (EntityType entity : entities) {
                logger.debug("Updating " + getDisplayEntityTypeName() + " " + getEntityInstanceName(entity));
                prepareEntityUpdate(entity, updatedByUserInfo);
            }
            getEntityDbFacade().edit(entities);
            for (EntityType entity : entities) {
                entity.setPersitanceErrorMessage(null);
                addCdbEntitySystemLog(SystemLogLevel.entityInfo, "Updated: " + entity.getSystemLogString(), updatedByUserInfo);
                publishMqttEvent(new UpdateEvent(entity, "Update action completed"));
            }
            clearCaches();
        } catch (CdbException ex) {
            logger.error("Could not update " + getDisplayEntityTypeName() + " entities: " + ex.getMessage());
            setPersistenceErrorMessageForList(entities, ex.getMessage());
            addCdbEntityWarningSystemLog("Failed to update list of " + getDisplayEntityTypeName(), ex, null, updatedByUserInfo);
            throw ex;
        } catch (RuntimeException ex) {
            Throwable t = ExceptionUtils.getRootCause(ex);
            logger.error("Could not update list of " + getDisplayEntityTypeName() + ": " + t.getMessage());
            addCdbEntityWarningSystemLog("Failed to update list of " + getDisplayEntityTypeName(), ex, null, updatedByUserInfo);
            setPersistenceErrorMessageForList(entities, t.getMessage());
            throw ex;
        }
    }

    public void destroy(EntityType entity, UserInfo destroyedByUserInfo) throws CdbException, RuntimeException {
        try {
            prepareEntityDestroy(entity, destroyedByUserInfo);
            getEntityDbFacade().remove(entity);

            addCdbEntitySystemLog(SystemLogLevel.entityInfo, "Deleted: " + entity.getSystemLogString(), destroyedByUserInfo);
            publishMqttEvent(new DeleteEvent(entity, "Delete action completed"));

            clearCaches();
        } catch (CdbException ex) {
            entity.setPersitanceErrorMessage(ex.getMessage());
            addCdbEntityWarningSystemLog("Failed to destroy", ex, entity, destroyedByUserInfo);
            logger.error("Could not destroy " + getDisplayEntityTypeName() + " "
                    + getEntityInstanceName(entity) + ": " + ex.getMessage());
            throw ex;
        } catch (RuntimeException ex) {
            Throwable t = ExceptionUtils.getRootCause(ex);
            logger.error("Could not destroy " + getDisplayEntityTypeName() + " "
                    + getEntityInstanceName(entity) + ": " + t.getMessage());
            addCdbEntityWarningSystemLog("Failed to destroy", ex, entity, destroyedByUserInfo);
            entity.setPersitanceErrorMessage(t.getMessage());
            throw ex;
        }
    }

    public void destroyList(
            List<EntityType> entities,
            EntityType updateEntity, UserInfo destroyedByUserInfo)
            throws CdbException, RuntimeException {

        try {
            if (updateEntity != null) {
                prepareEntityUpdate(updateEntity, destroyedByUserInfo);
            }

            for (EntityType entity : entities) {
                if ((entity != null) && entity.getId() != null) {
                    prepareEntityDestroy(entity, destroyedByUserInfo);
                }
            }

            getEntityDbFacade().remove(entities, updateEntity);

            addCdbEntitySystemLog(SystemLogLevel.entityInfo, "Deleted: " + entities.size() + " entities.", destroyedByUserInfo);
            for (EntityType entity : entities) {
                publishMqttEvent(new DeleteEvent(entity, "Delete action completed"));
            }
            setPersistenceErrorMessageForList(entities, null);
            clearCaches();
        } catch (CdbException ex) {
            logger.error("Could not delete list of " + getDisplayEntityTypeName() + ": " + ex.getMessage());
            setPersistenceErrorMessageForList(entities, ex.getMessage());
            addCdbEntityWarningSystemLog("Failed to delete list of " + getDisplayEntityTypeName(), ex, updateEntity, destroyedByUserInfo);
            throw ex;
        } catch (RuntimeException ex) {
            logger.error("Could not delete list of " + getDisplayEntityTypeName() + ": " + ex.getMessage());
            setPersistenceErrorMessageForList(entities, ex.getMessage());
            addCdbEntityWarningSystemLog("Failed to delete list of " + getDisplayEntityTypeName(), ex, updateEntity, destroyedByUserInfo);
            throw ex;
        }
    }

    /**
     * On database operation clear cache of related cached entity when needed.
     */
    protected void clearCaches() {
    }

    /**
     * Find entity instance by id.
     *
     * @param id entity instance id
     * @return entity instance
     */
    public EntityType findById(Integer id) {
        return getEntityDbFacade().find(id);
    }

    /**
     * Used by import framework. Looks up entity by path. Default implementation
     * raises exception. Subclasses should override to provide support for
     * lookup by path.
     */
    public EntityType findByPath(String path) throws CdbException {
        throw new CdbException("controller utility does not support lookup by path");
    }

    public String getEntityInstanceName(EntityType entity) {
        if (entity != null) {
            return entity.toString();
        }
        return "";
    }

    public abstract String getEntityTypeName();

    public String getDisplayEntityTypeName() {
        String entityTypeName = getEntityTypeName();

        entityTypeName = entityTypeName.substring(0, 1).toUpperCase() + entityTypeName.substring(1);

        String displayEntityTypeName = "";

        int prevEnd = 0;
        for (int i = 1; i < entityTypeName.length(); i++) {
            Character c = entityTypeName.charAt(i);
            if (Character.isUpperCase(c)) {
                displayEntityTypeName += entityTypeName.substring(prevEnd, i) + " ";
                prevEnd = i;
            }
        }

        displayEntityTypeName += entityTypeName.substring(prevEnd);

        return displayEntityTypeName;
    }

    /**
     * Prepare entity insert.
     *
     * This method should be overridden in the derived controller.
     *
     * @param entity entity instance
     * @throws CdbException in case of any errors
     */
    protected void prepareEntityInsert(EntityType entity, UserInfo userInfo) throws CdbException {
    }

    /**
     * Prepare entity update.
     *
     * This method should be overridden in the derived controller.
     *
     * @param entity entity instance
     * @throws CdbException in case of any errors
     */
    protected void prepareEntityUpdate(EntityType entity, UserInfo updatedByUser) throws CdbException {
    }

    protected void prepareEntityUpdateOnRemoval(EntityType entity) throws CdbException {
    }

    protected void prepareEntityDestroy(EntityType entity, UserInfo userInfo) throws CdbException {
    }

    protected void addCreatedSystemLog(EntityType entity, UserInfo createdByUserInfo) throws CdbException {
        String message = "Created: " + entity.getSystemLogString();
        addCdbEntitySystemLog(SystemLogLevel.entityInfo, message, createdByUserInfo);
    }

    protected void addCreatedWarningSystemLog(Exception exception, EntityType entity, UserInfo createdByUserInfo) throws CdbException {
        addCdbEntityWarningSystemLog("Failed to create", exception, entity, createdByUserInfo);
    }

    /**
     * Allows the controller to quickly add a warning log entry while
     * automatically appending appropriate info.
     *
     * @param warningMessage - Generic warning message.
     * @param exception - [OPTIONAL] will append the message of the exception.
     * @param entity - [OPTIONAL] will append the toString of the entity.
     * @param sessionUser
     */
    protected void addCdbEntityWarningSystemLog(String warningMessage, Exception exception, CdbEntity entity, UserInfo sessionUser) throws CdbException {
        if (entity != null) {
            warningMessage += ": " + entity.toString();
        }
        if (exception != null) {
            warningMessage += ". Exception - " + exception.getMessage();
        }

        addCdbEntitySystemLog(SystemLogLevel.entityWarning, warningMessage, sessionUser);
    }

    /**
     * Allows the controller to quickly add a log entry to system logs with
     * current session user stamp.
     *
     * @param logLevel
     * @param message
     * @param sessionUser
     */
    protected void addCdbEntitySystemLog(SystemLogLevel logLevel, String message, UserInfo sessionUser) throws CdbException {
        if (sessionUser != null) {
            String username = sessionUser.getUsername();
            message = "User: " + username + " | " + message;
        }
        LogControllerUtility logControllerUtility = LogControllerUtility.getSystemLogInstance();
        logControllerUtility.addSystemLog(logLevel, message);
    }

    protected void setPersistenceErrorMessageForList(List<EntityType> entities, String msg) {
        for (EntityType entity : entities) {
            entity.setPersitanceErrorMessage(msg);
        }
    }

    public List<EntityType> getAllEntities() {
        return getEntityDbFacade().findAll();
    }

    public List<EntityType> searchEntities(String searchString, Map searchOpts) {
        return searchEntities(searchString);
    }

    public List<EntityType> searchEntities(String searchString) {
        return getEntityDbFacade().searchEntities(searchString);
    }

    public String generatePatternString(String searchString) {
        String patternString;
        if (searchString.contains("?") || searchString.contains("*")) {
            patternString = searchString.replace("*", ".*");
            patternString = patternString.replace("?", ".");
        } else {
            patternString = Pattern.quote(searchString);
        }
        return patternString;
    }

    public Pattern getSearchPattern(String patternString, boolean caseInsensitive) {
        Pattern searchPattern;
        if (caseInsensitive) {
            searchPattern = Pattern.compile(patternString, Pattern.CASE_INSENSITIVE);
        } else {
            searchPattern = Pattern.compile(patternString);
        }

        return searchPattern;
    }

    public LinkedList<SearchResult> performEntitySearch(String searchString, boolean caseInsensitive) {
        return performEntitySearch(searchString, null, caseInsensitive);
    }

    /**
     * Search all entities for a given string.
     *
     * @param searchString search string
     * @param caseInsensitive use case insensitive search
     * @return
     */
    public LinkedList<SearchResult> performEntitySearch(String searchString, Map searchOpts, boolean caseInsensitive) {
        LinkedList<SearchResult> searchResultList = new LinkedList<>();
        if (searchString == null || searchString.isEmpty()) {
            return searchResultList;
        }

        // Start new search                
        String patternString = generatePatternString(searchString);
        Pattern searchPattern = getSearchPattern(patternString, caseInsensitive);

        List<EntityType> allObjectList = searchEntities(searchString, searchOpts);
        for (EntityType entity : allObjectList) {
            try {
                SearchResult searchResult = entity.createSearchResultInfo(searchPattern);
                if (!searchResult.isEmpty()) {
                    searchResultList.add(searchResult);
                }
            } catch (RuntimeException ex) {
                logger.warn("Could not search entity " + entity.toString() + " (Error: " + ex.toString() + ")");
            }

        }

        return searchResultList;
    }

    public PropertyValue preparePropertyTypeValueAdd(EntityType cdbDomainEntity, PropertyType propertyType) {
        return preparePropertyTypeValueAdd(cdbDomainEntity, propertyType, propertyType.getDefaultValue(), null);
    }

    public PropertyValue preparePropertyTypeValueAdd(EntityType cdbDomainEntity,
            PropertyType propertyType, String propertyValueString, String tag) {
        // Implement in controller with entity info. 
        return null;
    }

    public PropertyValue preparePropertyTypeValueAdd(EntityType cdbEntity,
            PropertyType propertyType, String propertyValueString, String tag,
            UserInfo updatedByUser) {
        Date lastModifiedOnDateTime = new Date();

        PropertyValue propertyValue = new PropertyValue();
        propertyValue.setPropertyType(propertyType);
        propertyValue.setValue(propertyValueString);
        propertyValue.setUnits(propertyType.getDefaultUnits());
        cdbEntity.addPropertyValueToPropertyValueList(propertyValue);
        propertyValue.setEnteredByUser(updatedByUser);
        propertyValue.setEnteredOnDateTime(lastModifiedOnDateTime);
        if (tag != null) {
            propertyValue.setTag(tag);
        }

        cdbEntity.resetPropertyValueLists();

        // Get method called by GUI populates metadata
        // Needed for multi-edit or API to also populate metadata
        propertyValue.getPropertyValueMetadataList();

        return propertyValue;
    }

    public PropertyType prepareCableEndDesignationPropertyType() {

        PropertyTypeControllerUtility propertyTypeControllerUtility = new PropertyTypeControllerUtility();
        PropertyType propertyType = propertyTypeControllerUtility.createEntityInstance(null);

        propertyType.setIsInternal(true);
        propertyType.setName(CdbEntity.CABLE_END_DESIGNATION_PROPERTY_TYPE);
        propertyType.setDescription(CdbEntity.CABLE_END_DESIGNATION_PROPERTY_DESCRIPTION);

        try {
            propertyTypeControllerUtility.create(propertyType, null);
        } catch (CdbException ex) {
            logger.error(ex.getMessage());
            return null;
        }

        return propertyType;
    }

    /**
     * Returns name to use for ItemConnectors in UI. Subclasses override to
     * customize.
     *
     * @return
     */
    public String getDisplayItemConnectorName() {
        return "connector";
    }

    public String getDisplayItemConnectorLabel() {
        return StringUtility.capitalize(getDisplayItemConnectorName());
    }

    public String getDisplayItemConnectorsLabel() {
        String labelString = StringUtility.capitalize(getDisplayItemConnectorName());
        return labelString + "s";
    }

}
