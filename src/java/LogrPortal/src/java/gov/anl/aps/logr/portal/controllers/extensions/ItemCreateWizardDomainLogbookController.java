/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.extensions;

import gov.anl.aps.logr.portal.controllers.ItemController;
import gov.anl.aps.logr.portal.controllers.ItemDomainLogbookController;
import gov.anl.aps.logr.portal.utilities.SessionUtility;
import java.io.Serializable;
import javax.enterprise.context.SessionScoped;
import javax.inject.Named;
import org.primefaces.event.FlowEvent;

/**
 *
 * @author djarosz
 */
@Named(ItemCreateWizardDomainLogbookController.controllerNamed)
@SessionScoped
public class ItemCreateWizardDomainLogbookController extends ItemCreateWizardController implements Serializable {

    public final static String controllerNamed = "itemCreateWizardDomainLogbookController";   

    @Override
    public String getItemCreateWizardControllerNamed() {
        return controllerNamed; 
    }    
    
    ItemDomainLogbookController itemDomainController = null; 
    @Override
    public ItemController getItemController() {
        if (itemDomainController == null) {
            itemDomainController = ItemDomainLogbookController.getInstance(); 
        }
        return itemDomainController;         
    }
    
    public static ItemCreateWizardDomainLogbookController getInstance() {
        return (ItemCreateWizardDomainLogbookController) SessionUtility.findBean(controllerNamed);
    }
    
    @Override
    public String getFirstCreateWizardStep() {
        return ItemCreateWizardSteps.basicInformation.getValue();
    }            
    
    
}
