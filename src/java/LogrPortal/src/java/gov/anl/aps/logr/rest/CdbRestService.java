/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest;

/**
 *
 * @author djarosz
 */
import io.swagger.v3.jaxrs2.integration.resources.AcceptHeaderOpenApiResource;
import io.swagger.v3.jaxrs2.integration.resources.OpenApiResource;
import java.util.Set;
import javax.ws.rs.ApplicationPath;
import javax.ws.rs.core.Application;
import org.glassfish.jersey.jackson.JacksonFeature;

@ApplicationPath("/api/")
public class CdbRestService extends Application {

    public CdbRestService() {
        super();
    }

    @Override
    public Set<Class<?>> getClasses() {
        Set<Class<?>> restResourceClasses = getRestResourceClasses();

        // Swagger core v2.0
        restResourceClasses.add(OpenApiResource.class);
        restResourceClasses.add(AcceptHeaderOpenApiResource.class);

        // Add json processor 
        restResourceClasses.add(JacksonFeature.class);

        return restResourceClasses;
    }

    private Set<Class<?>> getRestResourceClasses() {
        Set<Class<?>> resources = new java.util.HashSet<Class<?>>();
        resources.add(gov.anl.aps.logr.rest.authentication.AuthenticationFilter.class);
        resources.add(gov.anl.aps.logr.rest.provider.GenericAPIExceptionProvider.class);
        resources.add(gov.anl.aps.logr.rest.routes.AuthenticationRoute.class);        
        resources.add(gov.anl.aps.logr.rest.routes.DomainRoute.class);
        resources.add(gov.anl.aps.logr.rest.routes.DownloadRoute.class);
        resources.add(gov.anl.aps.logr.rest.routes.LogbookRoute.class);
        resources.add(gov.anl.aps.logr.rest.routes.NotificationConfigurationRoute.class);
        resources.add(gov.anl.aps.logr.rest.routes.PropertyValueRoute.class);
        resources.add(gov.anl.aps.logr.rest.routes.SearchRoute.class);       
        resources.add(gov.anl.aps.logr.rest.routes.SystemLogRoute.class);
        resources.add(gov.anl.aps.logr.rest.routes.TestRoute.class);
        resources.add(gov.anl.aps.logr.rest.routes.UsersRoute.class);
        return resources;
    }

}
