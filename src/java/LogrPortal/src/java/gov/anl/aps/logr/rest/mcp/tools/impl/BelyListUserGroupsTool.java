/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp.tools.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import gov.anl.aps.logr.portal.model.db.entities.UserGroup;
import gov.anl.aps.logr.rest.mcp.render.McpRenderLimits;
import gov.anl.aps.logr.rest.mcp.schema.JsonSchemaBuilder;
import gov.anl.aps.logr.rest.mcp.tools.AbstractMcpTool;
import gov.anl.aps.logr.rest.mcp.tools.McpArgumentException;
import gov.anl.aps.logr.rest.mcp.tools.McpToolContext;
import gov.anl.aps.logr.rest.mcp.tools.McpToolResult;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;

import static gov.anl.aps.logr.rest.mcp.render.McpTextRenderer.nz;
import static gov.anl.aps.logr.rest.mcp.render.McpTextRenderer.safe;

/** Lists user groups, optionally filtered by name substring. */
public class BelyListUserGroupsTool extends AbstractMcpTool {

    @Override
    public String getName() {
        return "bely_list_user_groups";
    }

    @Override
    public String getTitle() {
        return "List BELY user groups";
    }

    @Override
    public String getDescription() {
        return "List user groups, optionally filtered by a name substring.";
    }

    @Override
    public ObjectNode getInputSchema() {
        return new JsonSchemaBuilder()
                .stringProp("name", "Case-insensitive substring to match against the group name")
                .integerProp("limit", "Maximum rows to return (default " + McpRenderLimits.DEFAULT_ROW_LIMIT
                        + ", max " + McpRenderLimits.MAX_ROW_LIMIT + ")")
                .build();
    }

    @Override
    public McpToolResult call(JsonNode args, McpToolContext ctx) throws McpArgumentException {
        String name = optString(args, "name");
        int limit = optIntInRange(args, "limit", McpRenderLimits.DEFAULT_ROW_LIMIT, 1, McpRenderLimits.MAX_ROW_LIMIT);

        List<UserGroup> matches;
        if (name == null || name.isEmpty()) {
            matches = ctx.getUserGroupFacade().findAll();
        } else {
            UserGroup exact = ctx.getUserGroupFacade().findByName(name);
            if (exact != null) {
                matches = Collections.singletonList(exact);
            } else {
                matches = substringFilter(ctx.getUserGroupFacade().findAll(), name);
            }
        }

        return McpToolResult.text(render(name, matches, limit));
    }

    private List<UserGroup> substringFilter(List<UserGroup> all, String name) {
        String needle = name.toLowerCase(Locale.ROOT);
        List<UserGroup> result = new ArrayList<>();
        for (UserGroup g : all) {
            if (g.getName() != null && g.getName().toLowerCase(Locale.ROOT).contains(needle)) {
                result.add(g);
            }
        }
        return result;
    }

    private String render(String name, List<UserGroup> matches, int limit) {
        StringBuilder sb = new StringBuilder();
        sb.append("User groups").append(name == null || name.isEmpty() ? "" : " matching \"" + name + "\"")
                .append(" (").append(matches.size()).append(")\n");

        int shown = Math.min(limit, matches.size());
        for (int i = 0; i < shown; i++) {
            UserGroup g = matches.get(i);
            sb.append("- id=").append(g.getId())
                    .append(" | ").append(nz(g.getName()))
                    .append(" | ").append(safe(() -> nz(g.getDescription())))
                    .append("\n");
        }
        if (matches.size() > shown) {
            sb.append("… showing ").append(shown).append(" of ").append(matches.size())
                    .append("; increase limit (max ").append(McpRenderLimits.MAX_ROW_LIMIT).append(") or narrow filter\n");
        }

        return sb.toString();
    }
}
