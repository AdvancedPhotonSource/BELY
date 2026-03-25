/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.jsf.beans;

import gov.anl.aps.logr.portal.model.db.entities.Attachment;
import gov.anl.aps.logr.portal.model.db.entities.Log;
import gov.anl.aps.logr.portal.utilities.LogAttachmentUtility;
import gov.anl.aps.logr.portal.utilities.SessionUtility;
import java.io.IOException;
import java.io.Serializable;
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
        try {
            if (uploadedFile != null && !uploadedFile.getFileName().isEmpty()) {
                String fileName = uploadedFile.getFileName();
                Attachment attachment = LogAttachmentUtility.uploadAttachment(
                        uploadedFile.getInputStream(), fileName, logEntry);
                String fileReference = LogAttachmentUtility.buildMarkdownReference(fileName, attachment);

                if (attachFileReference) {
                    String text = logEntry.getText();
                    text += "\n\n" + fileReference;
                    logEntry.setText(text);
                }

                SessionUtility.addInfoMessage("Success", "Uploaded file " + fileName + ".");
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
