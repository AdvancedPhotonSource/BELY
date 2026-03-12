/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.routes;

import gov.anl.aps.logr.rest.authentication.Secured;
import gov.anl.aps.logr.rest.entities.ApiExceptionMessage;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import javax.ws.rs.GET;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.core.MediaType;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

/**
 *
 * @author djarosz
 */
@Path("/Test")
@Tag(name = "Test")
public class TestRoute {
    
    private static final Logger LOGGER = LogManager.getLogger(TestRoute.class.getName());
    
    @GET
    @Path("/Auth")
    @Operation(responses = {@ApiResponse(responseCode = "200", description = "OK", useReturnTypeSchema = true)})
    @Produces(MediaType.APPLICATION_JSON)
    @SecurityRequirement(name = "belyAuth")
    @Secured
    public boolean verifyAuthenticated() {
        LOGGER.debug("User is authenticated.");
        return true; 
    }
    
    @GET
    @Path("/NoAuth")
    @Operation(responses = {@ApiResponse(responseCode = "200", description = "OK", useReturnTypeSchema = true)})
    @Produces(MediaType.APPLICATION_JSON)
    public boolean verifyConnection() {
        LOGGER.debug("User is connected.");
        return true; 
    }
    
    @GET
    @Path("/SampleErrorMessage")
    @Operation(responses = {@ApiResponse(responseCode = "200", description = "OK", useReturnTypeSchema = true)})
    @Produces(MediaType.APPLICATION_JSON)
    public ApiExceptionMessage getSampleErrorMessage() {
        Exception exception = new Exception("Sample Exception Message");         
        ApiExceptionMessage apiExceptionMessage = new ApiExceptionMessage(exception);
        
        LOGGER.debug("Generating sample exception.");
        
        return apiExceptionMessage;
    }
    
}
