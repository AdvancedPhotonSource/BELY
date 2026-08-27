/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp.tools.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import gov.anl.aps.logr.portal.model.db.entities.Item;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook;
import gov.anl.aps.logr.rest.entities.LogEntry;
import gov.anl.aps.logr.rest.mcp.render.McpRenderLimits;
import gov.anl.aps.logr.rest.mcp.schema.JsonSchemaBuilder;
import gov.anl.aps.logr.rest.mcp.tools.AbstractMcpTool;
import gov.anl.aps.logr.rest.mcp.tools.McpArgumentException;
import gov.anl.aps.logr.rest.mcp.tools.McpToolContext;
import gov.anl.aps.logr.rest.mcp.tools.McpToolResult;
import java.util.List;

import static gov.anl.aps.logr.rest.mcp.render.McpTextRenderer.isoDate;
import static gov.anl.aps.logr.rest.mcp.render.McpTextRenderer.nz;
import static gov.anl.aps.logr.rest.mcp.render.McpTextRenderer.truncateWithMarker;

/** Lists a page of log entries for one document (or section), bodies truncated with a fetch-in-full marker. */
public class BelyListLogEntriesTool extends AbstractMcpTool {

    @Override
    public String getName() {
        return "bely_list_log_entries";
    }

    @Override
    public String getTitle() {
        return "List BELY log entries";
    }

    @Override
    public String getDescription() {
        return "List log entries in one log document (or section), oldest first, with bodies truncated "
                + "to maxBodyChars. Use offset/limit to page through more, and bely_get_log_entry for a "
                + "single entry in full (including replies and attachments).";
    }

    @Override
    public ObjectNode getInputSchema() {
        return new JsonSchemaBuilder()
                .requiredIntegerProp("logDocumentId", "Log document (or section) id")
                .integerProp("offset", "Number of entries to skip (default 0)")
                .integerProp("limit", "Maximum entries to return (default " + McpRenderLimits.DEFAULT_ENTRY_LIMIT
                        + ", max " + McpRenderLimits.MAX_ENTRY_LIMIT + ")")
                .integerProp("maxBodyChars", "Maximum characters of each entry body to include (default "
                        + McpRenderLimits.DEFAULT_ENTRY_BODY_CHARS + ", max " + McpRenderLimits.MAX_ENTRY_BODY_CHARS + ")")
                .booleanProp("includeReplies", "Include each entry's reply count (default false)")
                .booleanProp("includeReactions", "Load reactions (not rendered in the list; use bely_get_log_entry to see them) (default false)")
                .build();
    }

    @Override
    public McpToolResult call(JsonNode args, McpToolContext ctx) throws McpArgumentException {
        int logDocumentId = reqInteger(args, "logDocumentId");
        int offset = optIntInRange(args, "offset", 0, 0, Integer.MAX_VALUE);
        int limit = optIntInRange(args, "limit", McpRenderLimits.DEFAULT_ENTRY_LIMIT, 1, McpRenderLimits.MAX_ENTRY_LIMIT);
        int maxBodyChars = optIntInRange(args, "maxBodyChars", McpRenderLimits.DEFAULT_ENTRY_BODY_CHARS, 1, McpRenderLimits.MAX_ENTRY_BODY_CHARS);
        boolean includeReplies = optBoolean(args, "includeReplies", false);
        boolean includeReactions = optBoolean(args, "includeReactions", false);

        Item item = ctx.getItemFacade().findById(logDocumentId);
        if (!(item instanceof ItemDomainLogbook)) {
            return McpToolResult.error("No log document found with logDocumentId " + logDocumentId);
        }
        ItemDomainLogbook doc = (ItemDomainLogbook) item;

        List<LogEntry> entries = LogEntry.createLogEntryList(doc, includeReplies, includeReactions);
        int total = entries.size();
        if (offset >= total) {
            return McpToolResult.text("Log document " + logDocumentId + " \"" + nz(doc.getName()) + "\"\n"
                    + "Entries 0 of " + total + "  (offset=" + offset + " is past the end)\n");
        }
        int end = Math.min(total, offset + limit);
        List<LogEntry> page = entries.subList(offset, end);

        return McpToolResult.text(render(doc, page, offset, end, total, limit, maxBodyChars, includeReplies));
    }

    private String render(ItemDomainLogbook doc, List<LogEntry> page, int offset, int end, int total,
            int limit, int maxBodyChars, boolean includeReplies) {
        StringBuilder sb = new StringBuilder();
        sb.append("Log document ").append(doc.getId()).append(" \"").append(nz(doc.getName())).append("\"\n");
        sb.append("Entries ").append(offset + 1).append("-").append(end).append(" of ").append(total)
                .append("  (offset=").append(offset).append(", limit=").append(limit)
                .append(", maxBodyChars=").append(maxBodyChars).append(")\n");

        for (LogEntry entry : page) {
            String body = nz(entry.getLogEntry());
            String rendered = truncateWithMarker(body, maxBodyChars,
                    "call bely_get_log_entry logDocumentId=" + doc.getId() + " logId=" + entry.getLogId() + " for full text");
            sb.append("\n--- logId ").append(entry.getLogId())
                    .append(" | ").append(nz(entry.getEnteredByUsername()))
                    .append(" | entered ").append(isoDate(entry.getEnteredOnDateTime()));
            if (includeReplies) {
                List<LogEntry> replies = entry.getLogReplies();
                sb.append(" | replies ").append(replies == null ? 0 : replies.size());
            }
            sb.append("\n").append(rendered).append("\n");
        }

        if (end < total) {
            sb.append("\n… showing ").append(end - offset).append(" of ").append(total)
                    .append(" entries; call again with offset=").append(end).append(" to continue\n");
        }

        return sb.toString();
    }
}
