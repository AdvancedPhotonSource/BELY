/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.routes;

import gov.anl.aps.logr.common.constants.CdbPropertyValue;
import gov.anl.aps.logr.common.exceptions.InvalidRequest;
import gov.anl.aps.logr.common.exceptions.ObjectNotFound;
import gov.anl.aps.logr.portal.model.db.beans.AttachmentFacade;
import gov.anl.aps.logr.portal.model.db.beans.PropertyValueFacade;
import gov.anl.aps.logr.portal.model.db.entities.Attachment;
import gov.anl.aps.logr.portal.model.db.entities.PropertyTypeHandler;
import gov.anl.aps.logr.portal.model.db.entities.PropertyValue;
import gov.anl.aps.logr.portal.model.jsf.handlers.DocumentPropertyTypeHandler;
import gov.anl.aps.logr.portal.model.jsf.handlers.ImagePropertyTypeHandler;
import gov.anl.aps.logr.portal.utilities.GalleryUtility;
import gov.anl.aps.logr.portal.utilities.StorageUtility;
import gov.anl.aps.logr.rest.constants.DownloadRouteMimeType;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import javax.ejb.EJB;
import javax.ejb.EJBException;
import javax.ws.rs.GET;
import javax.ws.rs.Path;
import javax.ws.rs.PathParam;
import javax.ws.rs.Produces;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;
import javax.ws.rs.core.Response.ResponseBuilder;
import gov.anl.aps.logr.rest.entities.AttachmentChecksum;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

/**
 *
 * @author djarosz
 */
@Path("/Downloads")
@Tag(name = "Downloads")
public class DownloadRoute extends BaseRoute {

    private static final Logger LOGGER = LogManager.getLogger(DownloadRoute.class.getName());            

    @EJB
    PropertyValueFacade propertyValueFacade;
    
    @EJB
    AttachmentFacade attachmentFacade; 

    @GET
    @Path("/PropertyValue/Image/{imageName}/{scaling}")
    @Operation(responses = {@ApiResponse(responseCode = "200", description = "OK", useReturnTypeSchema = true)})
    public Response getImage(@PathParam("imageName") String imageName, @PathParam("scaling") String scaling) throws FileNotFoundException {
        LOGGER.debug("Fetching " + scaling + " image: " + imageName);
        String fullImageName = imageName + "." + scaling;
        String filePath = StorageUtility.getFileSystemPropertyValueImagePath(fullImageName);

        return getFileResponse("Image: " + fullImageName, imageName, filePath, true);
    }

    @GET
    @Path("/PropertyValue/{propertyValueId}")
    @Operation(responses = {@ApiResponse(responseCode = "200", description = "OK", useReturnTypeSchema = true)})
    @Produces("image/png")
    public Response getDownloadByPropertyValueId(@PathParam("propertyValueId") Integer propertyValueId) throws FileNotFoundException, ObjectNotFound, InvalidRequest {
        PropertyValue result = propertyValueFacade.find(propertyValueId);
        if (result == null) {
            throw new ObjectNotFound("Could not find a property value with id: " + propertyValueId);
        }

        String storedFileName = result.getValue();
        String originalFileName = result.getDisplayValue();        
        if (originalFileName == null) {
            originalFileName = storedFileName; 
        }

        PropertyTypeHandler propertyTypeHandler = result.getPropertyType().getPropertyTypeHandler();

        // false is document, true is image 
        Boolean isAttachment = null;
        String filePath = "";        

        if (propertyTypeHandler != null) {
            String name = propertyTypeHandler.getName();
            String documentHandlerName = DocumentPropertyTypeHandler.HANDLER_NAME;
            String imageHandlerName = ImagePropertyTypeHandler.HANDLER_NAME;

            String imageFormat = GalleryUtility.getImageFormat(originalFileName);           

            if (name.equals(documentHandlerName)) {
                if (GalleryUtility.viewableFormat(imageFormat) || imageFormat.equalsIgnoreCase("html")) {
                    isAttachment = false;
                } else {
                    isAttachment = true;
                }
                filePath = StorageUtility.getFileSystemPropertyValueDocumentPath(storedFileName);
            } else if (name.equals(imageHandlerName)) {
                isAttachment = false;
                String scaling = CdbPropertyValue.ORIGINAL_IMAGE_EXTENSION;
                LOGGER.debug("Fetching " + scaling + " image: " + originalFileName);
                String fullImageName = storedFileName + scaling;
                filePath = StorageUtility.getFileSystemPropertyValueImagePath(fullImageName);
            }
        }

        if (isAttachment == null) {
            throw new InvalidRequest("Property value provided is neither a document or image upload type property value.");
        }

        return getFileResponse("Upload: " + originalFileName, originalFileName, filePath, isAttachment);
    }
    
    @GET
    @Path("/Attachments/{attachmentName}")
    @Operation(responses = {@ApiResponse(responseCode = "200", description = "OK", useReturnTypeSchema = true)})
    public Response getAttachment(@PathParam("attachmentName") String attachmentName) throws FileNotFoundException {
        String originalAttachmentName = attachmentName; 
        Attachment att = null; 
        try{
            att = attachmentFacade.findByName(attachmentName);         
        } catch (EJBException ex) { }
        
        if (att != null) {
            // Set filename header to correct file name. 
            originalAttachmentName = att.getOriginalFilename(); 
        }
        
        String filePath = StorageUtility.getFileSystemLogAttachmentPath(attachmentName);
        return getFileResponse("Attachment: " + originalAttachmentName, originalAttachmentName, filePath, false);
    }
    
    @GET
    @Path("/Attachments/{attachmentName}/{scaling}")
    @Operation(responses = {@ApiResponse(responseCode = "200", description = "OK", useReturnTypeSchema = true)})
    @Produces("image/png")
    public Response getAttachment(@PathParam("attachmentName") String attachmentName, @PathParam("scaling") String scaling) throws FileNotFoundException {
        String fullAttachmentName = attachmentName + "." + scaling;
        String filePath = StorageUtility.getFileSystemLogAttachmentPath(fullAttachmentName);

        return getFileResponse("Image: " + fullAttachmentName, fullAttachmentName + ".png", filePath, false);
    }        

    @GET
    @Path("/Attachments/{attachmentName}/md5")
    @Operation(summary = "Calculate MD5 checksum for an attachment.", responses = {@ApiResponse(responseCode = "200", description = "OK", useReturnTypeSchema = true)})
    @Produces(MediaType.APPLICATION_JSON)
    public Response getAttachmentChecksum(@PathParam("attachmentName") String attachmentName) throws FileNotFoundException, ObjectNotFound {
        Attachment att = null;
        try {
            att = attachmentFacade.findByName(attachmentName);
        } catch (EJBException ex) { }

        if (att == null) {
            throw new ObjectNotFound("Could not find an attachment with name: " + attachmentName);
        }

        String filePath = StorageUtility.getFileSystemLogAttachmentPath(attachmentName);
        File file = new File(filePath);

        if (!file.exists()) {
            throw new FileNotFoundException("Attachment file not found on disk: " + attachmentName);
        }

        try {
            MessageDigest md = MessageDigest.getInstance("MD5");
            try (FileInputStream fis = new FileInputStream(file)) {
                byte[] buffer = new byte[8192];
                int bytesRead;
                while ((bytesRead = fis.read(buffer)) != -1) {
                    md.update(buffer, 0, bytesRead);
                }
            }
            byte[] digest = md.digest();
            StringBuilder sb = new StringBuilder();
            for (byte b : digest) {
                sb.append(String.format("%02x", b));
            }
            String checksum = sb.toString();

            AttachmentChecksum result = new AttachmentChecksum(att.getName(), att.getOriginalFilename(), checksum);
            return Response.ok(result).build();
        } catch (NoSuchAlgorithmException | IOException ex) {
            LOGGER.error(ex);
            return Response.serverError().entity("{\"error\": \"Failed to calculate checksum.\"}").type(MediaType.APPLICATION_JSON).build();
        }
    }

    private Response getFileResponse(String errorFileTypeColonName, String fileName, String storageFilePath, boolean isAttachment) throws FileNotFoundException {        
        File file = new File(storageFilePath);

        if (file.exists()) {
            // Callers may force a download; otherwise the resolved type decides.
            boolean forceDownload = isAttachment || !DownloadRouteMimeType.isInlineViewable(fileName);

            String headerObject = forceDownload ? "attachment; " : "inline; ";
            headerObject += buildFilenameHeaderParameters(fileName);
            
            ResponseBuilder response = null;
                        
            String typeForFilename = DownloadRouteMimeType.getTypeForFilename(fileName);                                
            response = Response.ok((Object) file, typeForFilename);            
            
            response.header("Content-Disposition",
                    headerObject);
            
            response.header("Content-Length", file.length()); 

            // Keep browsers from sniffing a different type than the one we declared.
            response.header("X-Content-Type-Options", "nosniff");
            
            return response.build();
        }

        FileNotFoundException fileNotFoundException = new FileNotFoundException(errorFileTypeColonName + " requested was not found.");
        LOGGER.error(fileNotFoundException);
        throw fileNotFoundException;
    }

    /** RFC 6266 filename parameters: quoted ASCII fallback plus RFC 5987 encoded form. */
    private String buildFilenameHeaderParameters(String fileName) {
        if (fileName == null || fileName.isEmpty()) {
            fileName = "download";
        }

        // Never let a path escape into the suggested name.
        fileName = fileName.replace('\\', '/');
        int lastSeparator = fileName.lastIndexOf('/');
        if (lastSeparator >= 0) {
            fileName = fileName.substring(lastSeparator + 1);
        }
        if (fileName.isEmpty()) {
            fileName = "download";
        }

        StringBuilder asciiFallback = new StringBuilder();
        for (char c : fileName.toCharArray()) {
            if (c < 32 || c > 126 || c == '"' || c == '\\') {
                asciiFallback.append('_');
            } else {
                asciiFallback.append(c);
            }
        }

        String encoded;
        try {
            encoded = URLEncoder.encode(fileName, StandardCharsets.UTF_8.name())
                    .replace("+", "%20");
        } catch (UnsupportedEncodingException ex) {
            // UTF-8 is always available.
            encoded = asciiFallback.toString();
        }

        return "filename=\"" + asciiFallback + "\"; filename*=UTF-8''" + encoded;
    }

}
