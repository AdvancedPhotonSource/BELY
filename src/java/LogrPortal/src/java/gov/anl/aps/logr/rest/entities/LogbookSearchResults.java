/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.entities;

import gov.anl.aps.logr.portal.utilities.SearchResult;
import java.util.LinkedList;

/**
 * API entity represents search results for log documents and log entries.
 *
 * @author djarosz
 */
public class LogbookSearchResults {

    private LinkedList<SearchResult> documentResults;
    private LinkedList<SearchResult> logEntryResults;

    public LogbookSearchResults() {
    }

    public LinkedList<SearchResult> getDocumentResults() {
        return documentResults;
    }

    public void setDocumentResults(LinkedList<SearchResult> documentResults) {
        this.documentResults = documentResults;
    }

    public LinkedList<SearchResult> getLogEntryResults() {
        return logEntryResults;
    }

    public void setLogEntryResults(LinkedList<SearchResult> logEntryResults) {
        this.logEntryResults = logEntryResults;
    }

}
