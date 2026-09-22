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

    private Integer id;
    private String markdownReference;
    private String downloadPath;
    private String originalFilename;
    private String storedFilename;

    public LogEntryAttachment() {
    }

    public LogEntryAttachment(Integer id, String markdownReference, String downloadPath, String originalFilename, String storedFilename) {
        this.id = id;
        this.markdownReference = markdownReference;
        this.downloadPath = downloadPath;
        this.originalFilename = originalFilename;
        this.storedFilename = storedFilename;
    }

    public Integer getId() {
        return id;
    }

    public void setId(Integer id) {
        this.id = id;
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
