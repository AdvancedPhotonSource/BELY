/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers;

import gov.anl.aps.logr.portal.controllers.settings.PropertyMetadataSettings;
import gov.anl.aps.logr.portal.controllers.utilities.PropertyMetadataControllerUtility;
import gov.anl.aps.logr.portal.model.db.entities.PropertyMetadata;
import gov.anl.aps.logr.portal.model.db.beans.PropertyMetadataFacade;
import gov.anl.aps.logr.portal.model.db.entities.PropertyValueBase;

import java.io.Serializable;
import javax.ejb.EJB;
import javax.inject.Named;
import javax.enterprise.context.SessionScoped;

@Named("propertyMetadataController")
@SessionScoped
public class PropertyMetadataController extends CdbEntityController<PropertyMetadataControllerUtility, PropertyMetadata, PropertyMetadataFacade, PropertyMetadataSettings> implements Serializable {

    @EJB
    private PropertyMetadataFacade propertyMetadataFacade; 
    
    private PropertyValueBase currentMetadataShown; 
    
    @Override
    protected PropertyMetadataSettings createNewSettingObject() {
        return new PropertyMetadataSettings(this); 
    }

    @Override
    protected PropertyMetadataFacade getEntityDbFacade() {
        return propertyMetadataFacade; 
    }

    public PropertyValueBase getCurrentMetadataShown() {
        return currentMetadataShown;
    }

    public void setCurrentMetadataShown(PropertyValueBase currentMetadataShown) {
        this.currentMetadataShown = currentMetadataShown;
    }

    @Override
    protected PropertyMetadataControllerUtility createControllerUtilityInstance() {
        return new PropertyMetadataControllerUtility(); 
    }
    
}
