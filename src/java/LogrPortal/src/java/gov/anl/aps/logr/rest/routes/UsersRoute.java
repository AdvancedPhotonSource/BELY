/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.routes;

import gov.anl.aps.logr.portal.model.db.beans.UserGroupFacade;
import gov.anl.aps.logr.portal.model.db.beans.UserInfoFacade;
import gov.anl.aps.logr.portal.model.db.entities.UserGroup;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
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
@Path("/Users")
@Tag(name = "Users")
public class UsersRoute extends BaseRoute {
    
    private static final Logger LOGGER = LogManager.getLogger(UsersRoute.class.getName());
    
    @EJB
    UserInfoFacade userInfoFacade; 
    
    @EJB
    UserGroupFacade userGroupFacade; 
    
    @GET
    @Path("/all")
    @Operation(responses = {@ApiResponse(responseCode = "200", description = "OK", useReturnTypeSchema = true)})
    @Produces(MediaType.APPLICATION_JSON)
    public List<UserInfo> getAll() { 
        LOGGER.debug("Fetching all users.");
        return userInfoFacade.findAll(); 
    }
    
    @GET
    @Path("/ByUsername/{username}")
    @Operation(responses = {@ApiResponse(responseCode = "200", description = "OK", useReturnTypeSchema = true)})
    @Produces(MediaType.APPLICATION_JSON)
    public UserInfo getUserByUsername(@PathParam("username") String username) {
        LOGGER.debug("Fetching user by username: " + username); 
        return userInfoFacade.findByUsername(username);
    }        
    
    @GET
    @Path("/allGroups")
    @Operation(responses = {@ApiResponse(responseCode = "200", description = "OK", useReturnTypeSchema = true)})
    @Produces(MediaType.APPLICATION_JSON)
    public List<UserGroup> getAllGroups() { 
        LOGGER.debug("Fetching all groups.");
        return userGroupFacade.findAll(); 
    }
    
    @GET
    @Path("/ByGroupName/{groupName}")
    @Operation(responses = {@ApiResponse(responseCode = "200", description = "OK", useReturnTypeSchema = true)})
    @Produces(MediaType.APPLICATION_JSON)
    public UserGroup getGroupByName(@PathParam("groupName") String groupName) {
        LOGGER.debug("Fetching user by username: " + groupName); 
        return userGroupFacade.findByName(groupName); 
    }           
}
