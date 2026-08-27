/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp.tools.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import gov.anl.aps.logr.portal.model.db.entities.Attachment;
import gov.anl.aps.logr.portal.model.db.entities.Item;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook;
import gov.anl.aps.logr.portal.model.db.entities.Log;
import gov.anl.aps.logr.portal.model.db.entities.LogReaction;
import gov.anl.aps.logr.rest.mcp.render.McpRenderLimits;
import gov.anl.aps.logr.rest.mcp.schema.JsonSchemaBuilder;
import gov.anl.aps.logr.rest.mcp.tools.AbstractMcpTool;
import gov.anl.aps.logr.rest.mcp.tools.McpArgumentException;
import gov.anl.aps.logr.rest.mcp.tools.McpToolContext;
import gov.anl.aps.logr.rest.mcp.tools.McpToolResult;
import java.util.List;
import java.util.Objects;

import static gov.anl.aps.logr.rest.mcp.render.McpTextRenderer.isoDate;
import static gov.anl.aps.logr.rest.mcp.render.McpTextRenderer.nz;
import static gov.anl.aps.logr.rest.mcp.render.McpTextRenderer.safe;
import static gov.anl.aps.logr.rest.mcp.render.McpTextRenderer.truncate;
import static gov.anl.aps.logr.rest.mcp.render.McpTextRenderer.truncateWithMarker;

/** Fetches one log entry in full, walking top-level logs then replies the same way {@code LogbookRoute} does. */
public class BelyGetLogEntryTool extends AbstractMcpTool {

    @Override
    public String getName() {
        return "bely_get_log_entry";
    }

    @Override
    public String getTitle() {
        return "Get BELY log entry";
    }

    @Override
    public String getDescription() {
        return "Fetch one log entry in full, with its attachments, and optionally its replies and reactions.";
    }

    @Override
    public ObjectNode getInputSchema() {
        return new JsonSchemaBuilder()
                .requiredIntegerProp("logDocumentId", "Log document (or section) id containing the entry")
                .requiredIntegerProp("logId", "Log entry id")
                .booleanProp("includeReplies", "Include full reply text (default true)")
                .booleanProp("includeReactions", "Include reactions (default false)")
                .booleanProp("includeAttachments", "Include attachment list with download paths (default true)")
                .build();
    }

    @Override
    public McpToolResult call(JsonNode args, McpToolContext ctx) throws McpArgumentException {
        int logDocumentId = reqInteger(args, "logDocumentId");
        int logId = reqInteger(args, "logId");
        boolean includeReplies = optBoolean(args, "includeReplies", true);
        boolean includeReactions = optBoolean(args, "includeReactions", false);
        boolean includeAttachments = optBoolean(args, "includeAttachments", true);

        Item item = ctx.getItemFacade().findById(logDocumentId);
        if (!(item instanceof ItemDomainLogbook)) {
            return McpToolResult.error("No log document found with logDocumentId " + logDocumentId);
        }
        ItemDomainLogbook doc = (ItemDomainLogbook) item;

        Log log = findLogInDocument(doc, logId);
        if (log == null) {
            return McpToolResult.error("Log id " + logId + " does not exist in log document " + logDocumentId + ".");
        }

        return McpToolResult.text(render(doc, log, includeReplies, includeReactions, includeAttachments));
    }

    private Log findLogInDocument(ItemDomainLogbook doc, int logId) {
        List<Log> logList = doc.getLogList();
        if (logList == null) {
            return null;
        }
        for (Log log : logList) {
            if (Objects.equals(log.getId(), logId)) {
                return log;
            }
            List<Log> children = log.getChildLogList();
            if (children != null) {
                for (Log reply : children) {
                    if (Objects.equals(reply.getId(), logId)) {
                        return reply;
                    }
                }
            }
        }
        return null;
    }

    private String render(ItemDomainLogbook doc, Log log, boolean includeReplies, boolean includeReactions, boolean includeAttachments) {
        StringBuilder sb = new StringBuilder();
        sb.append("logId ").append(log.getId()).append(" in log document ").append(doc.getId())
                .append(" \"").append(nz(doc.getName())).append("\"\n");
        sb.append("Entered ").append(isoDate(log.getEnteredOnDateTime()))
                .append(" by ").append(safe(() -> log.getEnteredByUser().getUsername())).append("\n");

        boolean modified;
        try {
            modified = log.isModifiedEntry();
        } catch (RuntimeException e) {
            modified = false;
        }
        if (modified) {
            sb.append("Last modified ").append(isoDate(log.getLastModifiedOnDateTime()))
                    .append(" by ").append(safe(() -> log.getLastModifiedByUser().getUsername())).append("\n");
        }

        sb.append("\n").append(truncate(nz(log.getText()), McpRenderLimits.MAX_SINGLE_ENTRY_CHARS)).append("\n");

        if (includeAttachments) {
            List<Attachment> attachments = log.getAttachmentList();
            if (attachments != null && !attachments.isEmpty()) {
                sb.append("\nAttachments (").append(attachments.size()).append(")\n");
                for (Attachment a : attachments) {
                    String filename = a.getOriginalFilename();
                    if (filename == null) {
                        filename = a.getName();
                    }
                    sb.append("- ").append(nz(filename)).append(" | /api/Downloads/Attachments/").append(nz(a.getName())).append("\n");
                }
            }
        }

        if (includeReactions) {
            List<LogReaction> reactions = log.getLogReactionList();
            if (reactions != null && !reactions.isEmpty()) {
                sb.append("\nReactions (").append(reactions.size()).append(")\n");
                for (LogReaction r : reactions) {
                    sb.append("- ").append(safe(() -> r.getReaction().getEmoji() + " " + r.getReaction().getName()))
                            .append(" by ").append(nz(r.getUsername())).append("\n");
                }
            }
        }

        if (includeReplies) {
            List<Log> replies = log.getChildLogList();
            if (replies != null && !replies.isEmpty()) {
                sb.append("\nReplies (").append(replies.size()).append(")\n");
                for (Log reply : replies) {
                    sb.append("--- logId ").append(reply.getId())
                            .append(" | ").append(safe(() -> reply.getEnteredByUser().getUsername()))
                            .append(" | ").append(isoDate(reply.getEnteredOnDateTime())).append("\n");
                    sb.append(truncateWithMarker(nz(reply.getText()), McpRenderLimits.DEFAULT_ENTRY_BODY_CHARS,
                            "call bely_get_log_entry logDocumentId=" + doc.getId() + " logId=" + reply.getId() + " for full text"))
                            .append("\n");
                }
            }
        }

        return sb.toString();
    }
}
