/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.jsf.beans;

import gov.anl.aps.logr.portal.model.db.entities.Attachment;
import gov.anl.aps.logr.portal.model.db.entities.Log;
import gov.anl.aps.logr.common.utilities.FileUtility;
import gov.anl.aps.logr.portal.utilities.GalleryUtility;
import gov.anl.aps.logr.portal.utilities.SessionUtility;
import gov.anl.aps.logr.portal.utilities.StorageUtility;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.Serializable;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.List;
import javax.enterprise.context.SessionScoped;
import javax.inject.Named;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.primefaces.event.FileUploadEvent;
import org.primefaces.model.file.UploadedFile;

/**
 * JSF bean for log attachment uploads.
 */
@Named("logAttachmentUploadBean")
@SessionScoped
public class LogAttachmentUploadBean implements Serializable {

    private static final Logger logger = LogManager.getLogger(LogAttachmentUploadBean.class.getName());

    private String lastFileReference;

    private Log logEntry;

    public Log getLogEntry() {
        return logEntry;
    }

    public void setLogEntry(Log logEntry) {
        this.logEntry = logEntry;
    }

    public String getLastFileReference() {
        return lastFileReference;
    }

    public void upload(UploadedFile uploadedFile) {
        upload(uploadedFile, true);
    }

    public String upload(UploadedFile uploadedFile, boolean attachFileReference) {
        Path uploadDirPath;
        try {
            if (uploadedFile != null && !uploadedFile.getFileName().isEmpty()) {
                String uploadedExtension = FileUtility.getFileExtension(uploadedFile.getFileName());

                uploadDirPath = Paths.get(StorageUtility.getFileSystemLogAttachmentsDirectory());
                logger.debug("Using log attachments directory: " + uploadDirPath.toString());
                if (Files.notExists(uploadDirPath)) {
                    Files.createDirectory(uploadDirPath);
                }
                File uploadDir = uploadDirPath.toFile();

                String originalExtension = "." + uploadedExtension;
                File originalFile = File.createTempFile("attachment.", originalExtension, uploadDir);
                InputStream input = uploadedFile.getInputStream();
                Files.copy(input, originalFile.toPath(), StandardCopyOption.REPLACE_EXISTING);
                logger.debug("Saved file: " + originalFile.toPath());
                Attachment attachment = new Attachment();
                attachment.setName(originalFile.getName());
                List<Attachment> attachmentList = logEntry.getAttachmentList();
                if (attachmentList == null) {
                    attachmentList = new ArrayList<>();
                    logEntry.setAttachmentList(attachmentList);
                }
                attachmentList.add(attachment);
                String fileName = uploadedFile.getFileName();
                String fileReference = "[" + fileName + "](" + attachment.getLogAttachmentPath() + ") ";
                if (GalleryUtility.viewableFileName(fileName)) {
                    fileReference = '!' + fileReference;
                    // Generate scaled images 
                    GalleryUtility.storeImagePreviews(originalFile, false);
                }

                if (attachFileReference) {
                    // TODO make configurable based on domain? 
                    String text = logEntry.getText();
                    String prefix = "\n\n";

                    text += prefix + fileReference;
                    logEntry.setText(text);
                }

                SessionUtility.addInfoMessage("Success", "Uploaded file " + uploadedFile.getFileName() + ".");
                return fileReference;
            }
        } catch (IOException ex) {
            logger.error(ex);
            SessionUtility.addErrorMessage("Error", ex.toString());
        }
        return "";
    }

    public void handleFileUpload(FileUploadEvent event) {
        upload(event.getFile());
    }

    public void handleFileUploadWithLastFileReference(FileUploadEvent event) {
        lastFileReference = upload(event.getFile(), false);
    }
}
