/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp.tools.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import gov.anl.aps.logr.portal.constants.ItemDomainName;
import gov.anl.aps.logr.portal.model.db.entities.EntityType;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook;
import gov.anl.aps.logr.rest.mcp.render.McpRenderLimits;
import gov.anl.aps.logr.rest.mcp.schema.JsonSchemaBuilder;
import gov.anl.aps.logr.rest.mcp.tools.AbstractMcpTool;
import gov.anl.aps.logr.rest.mcp.tools.McpArgumentException;
import gov.anl.aps.logr.rest.mcp.tools.McpToolContext;
import gov.anl.aps.logr.rest.mcp.tools.McpToolResult;
import java.util.List;

import static gov.anl.aps.logr.rest.mcp.render.McpTextRenderer.isoDate;
import static gov.anl.aps.logr.rest.mcp.render.McpTextRenderer.nz;
import static gov.anl.aps.logr.rest.mcp.render.McpTextRenderer.safe;

/** Lists log documents of a given logbook type, newest last-modified first. */
public class BelyListLogDocumentsTool extends AbstractMcpTool {

    @Override
    public String getName() {
        return "bely_list_log_documents";
    }

    @Override
    public String getTitle() {
        return "List BELY log documents";
    }

    @Override
    public String getDescription() {
        return "List log documents of a given logbook type, newest last-modified first. "
                + "Use bely_list_lookups kind=logbookTypes to find the type id.";
    }

    @Override
    public ObjectNode getInputSchema() {
        return new JsonSchemaBuilder()
                .requiredIntegerProp("logbookTypeId", "Logbook type id (see bely_list_lookups kind=logbookTypes)")
                .integerProp("limit", "Maximum rows to return (default " + McpRenderLimits.DEFAULT_ROW_LIMIT
                        + ", max " + McpRenderLimits.MAX_ROW_LIMIT + ")")
                .build();
    }

    @Override
    public McpToolResult call(JsonNode args, McpToolContext ctx) throws McpArgumentException {
        int logbookTypeId = reqInteger(args, "logbookTypeId");
        int limit = optIntInRange(args, "limit", McpRenderLimits.DEFAULT_ROW_LIMIT, 1, McpRenderLimits.MAX_ROW_LIMIT);

        List<EntityType> types = ctx.getLogbookTypes();
        EntityType type = types.stream().filter(t -> t.getId().equals(logbookTypeId)).findFirst().orElse(null);
        if (type == null) {
            return McpToolResult.error("Unknown logbookTypeId " + logbookTypeId + ". Valid ids: " + describeEntityTypes(types));
        }

        String domainName = ItemDomainName.logbook.getValue();
        List<ItemDomainLogbook> documents = ctx.getItemDomainLogbookFacade()
                .findByDomainNameAndEntityTypeOrderByLastModifiedDate(domainName, type.getName(), limit);

        return McpToolResult.text(render(type, documents, limit));
    }

    private String render(EntityType type, List<ItemDomainLogbook> documents, int limit) {
        StringBuilder sb = new StringBuilder();
        sb.append("Log documents of type \"").append(type.getName()).append("\" (id=").append(type.getId()).append(")\n");
        sb.append("Showing ").append(documents.size()).append(" (limit=").append(limit).append(")\n\n");

        for (ItemDomainLogbook doc : documents) {
            sb.append("- logDocumentId=").append(doc.getId())
                    .append(" | ").append(nz(doc.getName()))
                    .append(" | system=").append(safe(doc::getItemTypeString))
                    .append(" | modified ").append(safe(() -> isoDate(doc.getEntityInfo().getLastModifiedOnDateTime())))
                    .append("\n");
        }

        if (documents.size() >= limit) {
            sb.append("\n… result count equals the limit; more may exist — increase limit (max ")
                    .append(McpRenderLimits.MAX_ROW_LIMIT).append(") to check\n");
        }

        return sb.toString();
    }
}
