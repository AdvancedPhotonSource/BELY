/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.utilities;

import com.vladsch.flexmark.pdf.converter.PdfConverterExtension;
import com.vladsch.flexmark.util.data.MutableDataSet;
import gov.anl.aps.logr.portal.model.db.entities.EntityInfo;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook;
import gov.anl.aps.logr.portal.model.db.entities.Log;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import org.primefaces.model.DefaultStreamedContent;
import org.primefaces.model.StreamedContent;

/** Builds PDF downloads for log entries and log documents. */
public final class LogbookPdfExportUtility {

    private static final SimpleDateFormat DATE_FORMAT = new SimpleDateFormat("MM/dd/yyyy hh:mm a");

    private LogbookPdfExportUtility() {
    }

    public static StreamedContent exportEntry(ItemDomainLogbook document, Log log) throws IOException {
        byte[] pdf = renderPdf(buildEntryHtml(document, log));
        return stream(pdf, getEntryFilename(log));
    }

    public static StreamedContent exportDocument(ItemDomainLogbook document) throws IOException {
        byte[] pdf = renderPdf(buildDocumentHtml(document));
        return stream(pdf, getDocumentFilename(document));
    }

    static String buildEntryHtml(ItemDomainLogbook document, Log log) {
        StringBuilder html = startHtml("Log Entry " + log.getId());
        html.append("<div class=\"document-metadata\">");
        appendMetadata(html, "Document ID", document.getId());
        html.append("</div>");
        appendEntry(html, log, false);
        return finishHtml(html);
    }

    static String buildDocumentHtml(ItemDomainLogbook document) {
        StringBuilder html = startHtml(document.getName());
        html.append("<h1>").append(escape(document.getName())).append("</h1>");
        appendDocumentMetadata(html, document);

        List<ItemDomainLogbook> sections = document.getLogbookSections();
        if (sections == null || sections.isEmpty()) {
            appendEntries(html, document.getLogList());
        } else {
            for (ItemDomainLogbook section : sections) {
                html.append("<section class=\"logbook-section\"><h2>")
                        .append(escape(section.getName())).append("</h2>");
                appendEntries(html, section.getLogList());
                html.append("</section>");
            }
        }
        return finishHtml(html);
    }

    private static void appendDocumentMetadata(StringBuilder html, ItemDomainLogbook document) {
        EntityInfo info = document.getEntityInfo();
        html.append("<div class=\"document-metadata\">");
        appendMetadata(html, "Document ID", document.getId());
        appendMetadata(html, "Type", document.getEntityTypeString());
        if (info != null) {
            appendMetadata(html, "Created", format(info.getCreatedOnDateTime()));
            appendMetadata(html, "Created by", info.getCreatedByDisplayName());
            appendMetadata(html, "Last modified", format(info.getLastModifiedOnDateTime()));
            appendMetadata(html, "Last modified by", info.getLastModifiedByDisplayName());
        }
        html.append("</div>");
    }

    private static void appendEntries(StringBuilder html, List<Log> entries) {
        if (entries == null) {
            return;
        }
        for (Log entry : entries) {
            appendEntry(html, entry, false);
            List<Log> replies = entry.getChildLogList();
            if (replies != null) {
                for (Log reply : replies) {
                    appendEntry(html, reply, true);
                }
            }
        }
    }

    private static void appendEntry(StringBuilder html, Log log, boolean reply) {
        html.append("<article class=\"").append(reply ? "log-entry reply" : "log-entry")
                .append("\"><div class=\"entry-metadata\">");
        appendMetadata(html, "Entry ID", log.getId());
        appendMetadata(html, "Added", format(log.getEnteredOnDateTime()));
        appendMetadata(html, "Author", log.getEnteredByUser() == null ? "" : log.getEnteredByUser().getUsername());
        if (log.getLogTopic() != null) {
            appendMetadata(html, "Topic", log.getLogTopic().getName());
        }
        if (log.isModifiedEntry()) {
            appendMetadata(html, "Edited", format(log.getLastModifiedOnDateTime()));
            appendMetadata(html, "Edited by", log.getLastModifiedByUser() == null ? "" : log.getLastModifiedByUser().getUsername());
        }
        html.append("</div><div class=\"entry-body\">")
                .append(MarkdownParser.parseMarkdownAsPdfHTML(log.getText()))
                .append("</div></article>");
    }

    private static void appendMetadata(StringBuilder html, String label, Object value) {
        if (value != null && !value.toString().isEmpty()) {
            html.append("<span><strong>").append(escape(label)).append(":</strong> ")
                    .append(escape(value.toString())).append("</span> ");
        }
    }

    private static StringBuilder startHtml(String title) {
        return new StringBuilder("<!DOCTYPE html><html><head><meta charset=\"UTF-8\"/><title>")
                .append(escape(title)).append("</title><style>")
                .append(".document-metadata,.entry-metadata{color:#555;font-size:9pt;margin-bottom:8px}")
                .append(".entry-metadata{background:#e9ecef;border-left:5px solid #555;padding:7px 9px}")
                .append(".document-metadata span,.entry-metadata span{margin-right:12px}")
                .append(".log-entry{padding:10px 0;page-break-inside:avoid}")
                .append(".reply{margin-left:24px;border-left:3px solid #ddd;padding-left:12px}")
                .append("img{max-width:450px;max-height:450px;width:auto;height:auto}")
                .append("</style></head><body>");
    }

    private static String finishHtml(StringBuilder html) {
        return html.append("</body></html>").toString();
    }

    static byte[] renderPdf(String html) throws IOException {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        PdfConverterExtension.exportToPdf(output, html, "", new MutableDataSet());
        byte[] pdf = output.toByteArray();
        if (pdf.length < 5 || pdf[0] != '%' || pdf[1] != 'P' || pdf[2] != 'D' || pdf[3] != 'F') {
            throw new IOException("PDF conversion failed");
        }
        return pdf;
    }

    private static StreamedContent stream(byte[] pdf, String filename) {
        return DefaultStreamedContent.builder()
                .name(filename)
                .contentType("application/pdf")
                .stream(() -> new java.io.ByteArrayInputStream(pdf))
                .build();
    }

    static String getEntryFilename(Log log) {
        return "log-entry-" + (log.getId() == null ? "new" : log.getId()) + ".pdf";
    }

    static String getDocumentFilename(ItemDomainLogbook document) {
        String name = sanitizeFilename(document.getName());
        if (name.isEmpty()) {
            name = "log-document";
        }
        return name + "-" + (document.getId() == null ? "new" : document.getId()) + ".pdf";
    }

    private static String sanitizeFilename(String value) {
        return value == null ? "" : value.trim().replaceAll("[^A-Za-z0-9._-]+", "-")
                .replaceAll("^-+|-+$", "");
    }

    private static synchronized String format(Date date) {
        return date == null ? "" : DATE_FORMAT.format(date);
    }

    private static String escape(String value) {
        if (value == null) {
            return "";
        }
        return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace("\"", "&quot;").replace("'", "&#39;");
    }
}
