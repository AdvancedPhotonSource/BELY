/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.entities;


/**
 * API entity with log document section information. 
 * 
 * @author djarosz
 */
public class LogDocumentSection {
    
    // Refers to section item id. 
    private Integer id; 
    private String name; 

    public LogDocumentSection() {
    }

    public LogDocumentSection(Integer id, String name) {
        this.id = id;
        this.name = name;
    }

    public Integer getId() {
        return id;
    }

    public void setId(Integer id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }               
}
