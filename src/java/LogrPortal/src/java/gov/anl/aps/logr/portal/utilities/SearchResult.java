/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.utilities;

import com.fasterxml.jackson.annotation.JsonIgnore;
import gov.anl.aps.logr.portal.model.db.entities.CdbEntity;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.regex.Pattern;

/**
 * Search result class.
 */
public class SearchResult {

    public static final String SEARCH_RESULT_ROW_STYLE = "searchResultRow"; 
    
    private final CdbEntity cdbEntity;
    private final CdbEntity additionalEntity; 
    private final Integer objectId;
    private final String objectName;    
    private String additionalAttribute; 
    private String rowStyle; 
    private HashMap<String, String> objectAttributeMatchMap = new HashMap();
    
    public SearchResult(CdbEntity cdbEntity, Integer objectId, String objectName) {
        this.cdbEntity = cdbEntity; 
        this.objectId = objectId;
        this.objectName = objectName;
        this.additionalEntity = null; 
    }

    public SearchResult(CdbEntity cdbEntity, Integer objectId, String objectName, CdbEntity additionalEntity) {
        this.cdbEntity = cdbEntity; 
        this.objectId = objectId;
        this.objectName = objectName;
        this.additionalEntity = additionalEntity; 
    }

    public SearchResult(SearchResult result) {
        this.cdbEntity = result.cdbEntity;
        this.objectId = result.objectId;
        this.objectName = result.objectName; 
        this.objectAttributeMatchMap = result.objectAttributeMatchMap; 
        this.additionalEntity = null; 
    }

    @JsonIgnore
    public CdbEntity getCdbEntity() {
        return cdbEntity;
    }

    public CdbEntity getAdditionalEntity() {
        return additionalEntity;
    }

    public Integer getObjectId() {
        return objectId;
    }

    public String getObjectName() {
        return objectName;
    }

    @JsonIgnore
    public String getRowStyle() {
        return rowStyle;
    }

    public void setRowStyle(String rowStyle) {
        this.rowStyle = rowStyle;
    }

    public void addAttributeMatch(String key, String value) {
        objectAttributeMatchMap.put(key, value);
    }

    public HashMap<String, String> getObjectAttributeMatchMap() {
        return objectAttributeMatchMap;
    }

    public void setObjectAttributeMatchMap(HashMap<String, String> objectAttributeMatchMap) {
        this.objectAttributeMatchMap = objectAttributeMatchMap;
    }
   
    public boolean isEmpty() {
        return objectAttributeMatchMap.isEmpty();
    }
    
    public String getAdditionalAttribute() {
        return additionalAttribute;
    }

    public void setAdditionalAttribute(String additionalAttribute) {
        this.additionalAttribute = additionalAttribute;
    }

    public boolean doesValueContainPattern(String key, Object value, Pattern searchPattern) {
        if (value != null) {
            return doesValueContainPattern(key, value.toString(), searchPattern);
        }
        return false;
    }

    public boolean doesValueContainPattern(String key, String value, Pattern searchPattern) {
        if (value == null || value.isEmpty()) {
            return false;
        }
        boolean searchResult = searchPattern.matcher(value).find();
        if (searchResult) {
            addAttributeMatch(key, value);
        }
        return searchResult;
    }
    
    public ArrayList<String> getShortDisplayList() {
        ArrayList<String> stringList = new ArrayList<>(); 
        
        for (String key : objectAttributeMatchMap.keySet()) {
            stringList.add(objectAttributeMatchMap.get(key));                             
        }
        
        return stringList; 
    }
    
    public ArrayList<String> getDisplayList() {
        ArrayList<String> stringList = new ArrayList<>(); 
        
        for (String key : objectAttributeMatchMap.keySet()) {
            String resultItem = String.format("%s: %s", key, objectAttributeMatchMap.get(key));
            stringList.add(resultItem); 
        }
        
        return stringList; 
    }

    public String getDisplay() {
        String result = "";
        String keyDelimiter = ": ";
        String entryDelimiter = "";
        for (String key : objectAttributeMatchMap.keySet()) {
            result += entryDelimiter + key + keyDelimiter + objectAttributeMatchMap.get(key);
            entryDelimiter = "; ";
        }
        return result;
    }
}
