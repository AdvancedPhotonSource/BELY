/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.entities;

/**
 * DTO representing an attachment checksum response for the REST API.
 *
 * @author djarosz
 */
public class AttachmentChecksum {

    private String name;
    private String originalFilename;
    private String md5;

    public AttachmentChecksum() {
    }

    public AttachmentChecksum(String name, String originalFilename, String md5) {
        this.name = name;
        this.originalFilename = originalFilename;
        this.md5 = md5;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getOriginalFilename() {
        return originalFilename;
    }

    public void setOriginalFilename(String originalFilename) {
        this.originalFilename = originalFilename;
    }

    public String getMd5() {
        return md5;
    }

    public void setMd5(String md5) {
        this.md5 = md5;
    }

}
