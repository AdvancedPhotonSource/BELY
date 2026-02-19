/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.routes;

import gov.anl.aps.logr.portal.model.db.beans.NotificationConfigurationFacade;
import gov.anl.aps.logr.portal.model.db.beans.NotificationHandlerConfigKeyFacade;
import gov.anl.aps.logr.portal.model.db.beans.NotificationProviderConfigKeyFacade;
import gov.anl.aps.logr.portal.model.db.beans.NotificationProviderFacade;
import gov.anl.aps.logr.portal.model.db.entities.NotificationConfiguration;
import gov.anl.aps.logr.portal.model.db.entities.NotificationHandlerConfigKey;
import gov.anl.aps.logr.portal.model.db.entities.NotificationProvider;
import gov.anl.aps.logr.portal.model.db.entities.NotificationProviderConfigKey;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.util.List;
import javax.ejb.EJB;
import javax.ws.rs.GET;
import javax.ws.rs.Path;
import javax.ws.rs.PathParam;
import javax.ws.rs.Produces;
import javax.ws.rs.core.MediaType;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

/**
 *
 * @author djarosz
 */
@Path("/NotificationConfigurations")
@Tag(name = "NotificationConfigurations")
public class NotificationConfigurationRoute extends BaseRoute {

    private static final Logger LOGGER = LogManager.getLogger(NotificationConfigurationRoute.class.getName());

    @EJB
    NotificationConfigurationFacade notificationConfigurationFacade;

    @EJB
    NotificationProviderFacade notificationProviderFacade;

    @EJB
    NotificationProviderConfigKeyFacade notificationProviderConfigKeyFacade;

    @EJB
    NotificationHandlerConfigKeyFacade notificationHandlerConfigKeyFacade;

    @GET
    @Path("/all")
    @Produces(MediaType.APPLICATION_JSON)
    public List<NotificationConfiguration> getAll() {
        LOGGER.debug("Fetching all notification configurations");
        return notificationConfigurationFacade.findAll();
    }

    @GET
    @Path("/ById/{id}")
    @Produces(MediaType.APPLICATION_JSON)
    public NotificationConfiguration getById(@PathParam("id") int id) {
        LOGGER.debug("Fetching notification configuration with id: " + id);
        return notificationConfigurationFacade.find(id);
    }

    @GET
    @Path("/ByName/{name}")
    @Produces(MediaType.APPLICATION_JSON)
    public List<NotificationConfiguration> getByName(@PathParam("name") String name) {
        LOGGER.debug("Fetching notification configurations with name: " + name);
        return notificationConfigurationFacade.findByName(name);
    }

    @GET
    @Path("/ByProviderId/{providerId}")
    @Produces(MediaType.APPLICATION_JSON)
    public List<NotificationConfiguration> getByProviderId(@PathParam("providerId") int providerId) {
        LOGGER.debug("Fetching notification configurations for provider id: " + providerId);
        NotificationProvider provider = notificationProviderFacade.find(providerId);
        return notificationConfigurationFacade.findByProvider(provider);
    }

    @GET
    @Path("/ByUsername/{username}")
    @Produces(MediaType.APPLICATION_JSON)
    public List<NotificationConfiguration> getByUsername(@PathParam("username") String username) {
        LOGGER.debug("Fetching notification configurations for user: " + username);
        UserInfo user = userFacade.findByUsername(username);
        return notificationConfigurationFacade.findByUser(user);
    }

    @GET
    @Path("/Providers")
    @Produces(MediaType.APPLICATION_JSON)
    public List<NotificationProvider> getAllProviders() {
        LOGGER.debug("Fetching all notification providers");
        return notificationProviderFacade.findAll();
    }

    @GET
    @Path("/ProviderById/{id}")
    @Produces(MediaType.APPLICATION_JSON)
    public NotificationProvider getProviderById(@PathParam("id") int id) {
        LOGGER.debug("Fetching notification provider with id: " + id);
        return notificationProviderFacade.find(id);
    }

    @GET
    @Path("/ProviderByName/{name}")
    @Produces(MediaType.APPLICATION_JSON)
    public NotificationProvider getProviderByName(@PathParam("name") String name) {
        LOGGER.debug("Fetching notification provider with name: " + name);
        return notificationProviderFacade.findByName(name);
    }

    @GET
    @Path("/ProviderConfigKeys/{providerId}")
    @Produces(MediaType.APPLICATION_JSON)
    public List<NotificationProviderConfigKey> getProviderConfigKeys(@PathParam("providerId") int providerId) {
        LOGGER.debug("Fetching config keys for provider id: " + providerId);
        NotificationProvider provider = notificationProviderFacade.find(providerId);
        return notificationProviderConfigKeyFacade.findByProvider(provider);
    }

    @GET
    @Path("/HandlerConfigKeys")
    @Produces(MediaType.APPLICATION_JSON)
    public List<NotificationHandlerConfigKey> getHandlerConfigKeys() {
        LOGGER.debug("Fetching all handler config keys");
        return notificationHandlerConfigKeyFacade.findAll();
    }

}
