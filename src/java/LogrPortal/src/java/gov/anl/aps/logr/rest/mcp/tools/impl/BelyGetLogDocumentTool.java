/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp.tools.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import gov.anl.aps.logr.portal.model.db.entities.Item;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook;
import gov.anl.aps.logr.portal.model.db.entities.Log;
import gov.anl.aps.logr.rest.mcp.schema.JsonSchemaBuilder;
import gov.anl.aps.logr.rest.mcp.tools.AbstractMcpTool;
import gov.anl.aps.logr.rest.mcp.tools.McpArgumentException;
import gov.anl.aps.logr.rest.mcp.tools.McpToolContext;
import gov.anl.aps.logr.rest.mcp.tools.McpToolResult;
import java.util.List;

import static gov.anl.aps.logr.rest.mcp.render.McpTextRenderer.isoDate;
import static gov.anl.aps.logr.rest.mcp.render.McpTextRenderer.nz;
import static gov.anl.aps.logr.rest.mcp.render.McpTextRenderer.safe;

/** Fetches one log document's header plus its section list (each section is itself a full {@code ItemDomainLogbook}). */
public class BelyGetLogDocumentTool extends AbstractMcpTool {

    @Override
    public String getName() {
        return "bely_get_log_document";
    }

    @Override
    public String getTitle() {
        return "Get BELY log document";
    }

    @Override
    public String getDescription() {
        return "Fetch a log document's header (type, system, dates) plus its list of sections. "
                + "Provide either logDocumentId or name. Follow up with bely_list_log_entries on the "
                + "document or a section's logDocumentId to read its entries.";
    }

    @Override
    public ObjectNode getInputSchema() {
        return new JsonSchemaBuilder()
                .integerProp("logDocumentId", "Log document id")
                .stringProp("name", "Log document name (exact match; used only if logDocumentId is omitted)")
                .build();
    }

    @Override
    public McpToolResult call(JsonNode args, McpToolContext ctx) throws McpArgumentException {
        Integer logDocumentId = optInteger(args, "logDocumentId");
        String name = optString(args, "name");
        if (logDocumentId == null && (name == null || name.isEmpty())) {
            throw new McpArgumentException("Provide either logDocumentId or name");
        }

        ItemDomainLogbook doc;
        if (logDocumentId != null) {
            Item item = ctx.getItemFacade().findById(logDocumentId);
            if (!(item instanceof ItemDomainLogbook)) {
                return McpToolResult.error("No log document found with logDocumentId " + logDocumentId);
            }
            doc = (ItemDomainLogbook) item;
        } else {
            List<ItemDomainLogbook> matches = ctx.getItemDomainLogbookFacade().findByName(name);
            if (matches == null || matches.isEmpty()) {
                return McpToolResult.error("No log document found with name \"" + name + "\"");
            }
            doc = matches.get(0);
        }

        return McpToolResult.text(render(doc));
    }

    private String render(ItemDomainLogbook doc) {
        StringBuilder sb = new StringBuilder();
        sb.append("Log document ").append(doc.getId()).append(" \"").append(nz(doc.getName())).append("\"\n");
        sb.append("Type: ").append(safe(doc::getLongEntityTypeString))
                .append(" | System: ").append(safe(doc::getItemTypeString)).append("\n");
        sb.append("Created ").append(safe(() -> isoDate(doc.getEntityInfo().getCreatedOnDateTime())))
                .append(" by ").append(safe(() -> doc.getEntityInfo().getCreatedByUsername()))
                .append(" | Last modified ").append(safe(() -> isoDate(doc.getEntityInfo().getLastModifiedOnDateTime())))
                .append("\n\n");

        List<ItemDomainLogbook> sections = doc.getLogbookSections();
        sb.append("Sections (").append(sections.size()).append(")\n");
        for (ItemDomainLogbook section : sections) {
            List<Log> logs = section.getLogList();
            int count = logs == null ? 0 : logs.size();
            sb.append("- ").append(nz(section.getName()))
                    .append(" (logDocumentId=").append(section.getId())
                    .append(", ").append(count).append(" entries)\n");
        }
        if (sections.isEmpty()) {
            sb.append("(no sections)\n");
        }
        sb.append("\nCall bely_list_log_entries with a section's logDocumentId to read its entries.\n");

        return sb.toString();
    }
}
