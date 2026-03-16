/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.entities;

/**
 * DTO representing a log entry attachment for the REST API.
 *
 * @author djarosz
 */
public class LogEntryAttachment {

    private String markdownReference;
    private String downloadPath;
    private String originalFilename;
    private String storedFilename;

    public LogEntryAttachment() {
    }

    public LogEntryAttachment(String markdownReference, String downloadPath, String originalFilename, String storedFilename) {
        this.markdownReference = markdownReference;
        this.downloadPath = downloadPath;
        this.originalFilename = originalFilename;
        this.storedFilename = storedFilename;
    }

    public String getMarkdownReference() {
        return markdownReference;
    }

    public void setMarkdownReference(String markdownReference) {
        this.markdownReference = markdownReference;
    }

    public String getDownloadPath() {
        return downloadPath;
    }

    public void setDownloadPath(String downloadPath) {
        this.downloadPath = downloadPath;
    }

    public String getOriginalFilename() {
        return originalFilename;
    }

    public void setOriginalFilename(String originalFilename) {
        this.originalFilename = originalFilename;
    }

    public String getStoredFilename() {
        return storedFilename;
    }

    public void setStoredFilename(String storedFilename) {
        this.storedFilename = storedFilename;
    }

}
