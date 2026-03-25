/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.utilities;

import gov.anl.aps.logr.common.utilities.FileUtility;
import gov.anl.aps.logr.portal.model.db.entities.Attachment;
import gov.anl.aps.logr.portal.model.db.entities.Log;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.List;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

/**
 * Shared utility for uploading log attachments. Used by both the JSF upload
 * bean and the REST API.
 *
 * @author djarosz
 */
public class LogAttachmentUtility {

    private static final Logger logger = LogManager.getLogger(LogAttachmentUtility.class.getName());

    /**
     * Save an uploaded file as a log attachment. Handles: saving to disk,
     * creating Attachment entity, linking to log, viewability check, and image
     * preview generation.
     *
     * @param inputStream the file input stream
     * @param fileName the original file name
     * @param logEntry the log entry to attach to
     * @return the created Attachment entity
     * @throws IOException if file operations fail
     */
    public static Attachment uploadAttachment(InputStream inputStream, String fileName, Log logEntry) throws IOException {
        String uploadedExtension = FileUtility.getFileExtension(fileName);

        Path uploadDirPath = Paths.get(StorageUtility.getFileSystemLogAttachmentsDirectory());
        logger.debug("Using log attachments directory: " + uploadDirPath.toString());
        if (Files.notExists(uploadDirPath)) {
            Files.createDirectory(uploadDirPath);
        }
        File uploadDir = uploadDirPath.toFile();

        String originalExtension = "." + uploadedExtension;
        File originalFile = File.createTempFile("attachment.", originalExtension, uploadDir);
        Files.copy(inputStream, originalFile.toPath(), StandardCopyOption.REPLACE_EXISTING);
        logger.debug("Saved file: " + originalFile.toPath());

        Attachment attachment = new Attachment();
        attachment.setName(originalFile.getName());
        attachment.setOriginalFilename(fileName);

        List<Attachment> attachmentList = logEntry.getAttachmentList();
        if (attachmentList == null) {
            attachmentList = new ArrayList<>();
            logEntry.setAttachmentList(attachmentList);
        }
        attachmentList.add(attachment);

        if (GalleryUtility.viewableFileName(fileName)) {
            GalleryUtility.storeImagePreviews(originalFile, false);
        }

        return attachment;
    }

    /**
     * Build a markdown reference string for an attachment. Returns
     * "![filename](path)" for viewable files, "[filename](path)" for others.
     *
     * @param originalFilename the original file name
     * @param attachment the attachment entity
     * @return the markdown reference string
     */
    public static String buildMarkdownReference(String originalFilename, Attachment attachment) {
        String ref = "[" + originalFilename + "](" + attachment.getLogAttachmentPath() + ") ";
        if (GalleryUtility.viewableFileName(originalFilename)) {
            ref = "!" + ref;
        }
        return ref;
    }

}
