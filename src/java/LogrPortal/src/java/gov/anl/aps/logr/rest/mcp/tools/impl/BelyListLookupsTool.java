/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp.tools.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import gov.anl.aps.logr.portal.constants.EntityTypeName;
import gov.anl.aps.logr.portal.constants.ItemDomainName;
import gov.anl.aps.logr.portal.model.db.entities.EntityType;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook;
import gov.anl.aps.logr.portal.model.db.entities.ItemType;
import gov.anl.aps.logr.rest.mcp.schema.JsonSchemaBuilder;
import gov.anl.aps.logr.rest.mcp.tools.AbstractMcpTool;
import gov.anl.aps.logr.rest.mcp.tools.McpArgumentException;
import gov.anl.aps.logr.rest.mcp.tools.McpToolContext;
import gov.anl.aps.logr.rest.mcp.tools.McpToolResult;
import java.util.List;

import static gov.anl.aps.logr.rest.mcp.render.McpTextRenderer.nz;

/** Enumerates the small, mostly-static lookup lists other tools reference by id: types, systems, templates. */
public class BelyListLookupsTool extends AbstractMcpTool {

    private static final String KIND_LOGBOOK_TYPES = "logbookTypes";
    private static final String KIND_SYSTEMS = "systems";
    private static final String KIND_TEMPLATES = "templates";

    @Override
    public String getName() {
        return "bely_list_lookups";
    }

    @Override
    public String getTitle() {
        return "List BELY lookups";
    }

    @Override
    public String getDescription() {
        return "List logbook types, systems, or document templates, with the ids other tools filter by.";
    }

    @Override
    public ObjectNode getInputSchema() {
        return new JsonSchemaBuilder()
                .requiredEnumProp("kind", "Which lookup list to return", KIND_LOGBOOK_TYPES, KIND_SYSTEMS, KIND_TEMPLATES)
                .build();
    }

    @Override
    public McpToolResult call(JsonNode args, McpToolContext ctx) throws McpArgumentException {
        String kind = reqString(args, "kind");
        switch (kind) {
            case KIND_LOGBOOK_TYPES:
                return McpToolResult.text(renderEntityTypes(ctx.getLogbookTypes()));
            case KIND_SYSTEMS:
                return McpToolResult.text(renderItemTypes(ctx.getLogbookSystems()));
            case KIND_TEMPLATES:
                return McpToolResult.text(renderTemplates(ctx));
            default:
                return McpToolResult.error("Unknown kind \"" + kind + "\". Valid values: "
                        + KIND_LOGBOOK_TYPES + ", " + KIND_SYSTEMS + ", " + KIND_TEMPLATES);
        }
    }

    private String renderEntityTypes(List<EntityType> types) {
        StringBuilder sb = new StringBuilder("Logbook types (").append(types.size()).append(")\n");
        for (EntityType t : types) {
            sb.append("- id=").append(t.getId()).append(" | ").append(nz(t.getName())).append("\n");
        }
        return sb.toString();
    }

    private String renderItemTypes(List<ItemType> types) {
        StringBuilder sb = new StringBuilder("Systems (").append(types.size()).append(")\n");
        for (ItemType t : types) {
            sb.append("- id=").append(t.getId()).append(" | ").append(nz(t.getName())).append("\n");
        }
        return sb.toString();
    }

    private String renderTemplates(McpToolContext ctx) {
        List<ItemDomainLogbook> templates = ctx.getItemDomainLogbookFacade()
                .findByDomainAndEntityTypeAndTopLevel(ItemDomainName.logbook.getValue(), EntityTypeName.template.getValue());
        StringBuilder sb = new StringBuilder("Document templates (").append(templates.size()).append(")\n");
        for (ItemDomainLogbook t : templates) {
            sb.append("- logDocumentId=").append(t.getId()).append(" | ").append(nz(t.getName())).append("\n");
        }
        return sb.toString();
    }
}
