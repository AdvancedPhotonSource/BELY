/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.constants;

public enum LogDocumentSettings {
        showTimestampKey("showTimestamps"),
        logTemplateModeKey("logMode"),
        logTemplateModeNoneVal("none"),
        logTemplateModeCopyVal("copy"),
        logTemplateModeTemplatePerEntryVal("template per entry");            

        private String value;

        private LogDocumentSettings(String value) {
            this.value = value;
        }

        public String getValue() {
            return value;
        }
    };
