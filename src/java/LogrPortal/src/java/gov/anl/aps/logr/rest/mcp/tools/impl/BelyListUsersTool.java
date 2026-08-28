/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp.tools.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
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

/** Lists users, optionally filtered by name substring: exact {@code findByUsername} first, then a substring scan. */
public class BelyListUsersTool extends AbstractMcpTool {

    @Override
    public String getName() {
        return "bely_list_users";
    }

    @Override
    public String getTitle() {
        return "List BELY users";
    }

    @Override
    public String getDescription() {
        return "List users, optionally filtered by a username/first/last name substring.";
    }

    @Override
    public ObjectNode getInputSchema() {
        return new JsonSchemaBuilder()
                .stringProp("filter", "Case-insensitive substring to match against username, first name, or last name")
                .integerProp("limit", "Maximum rows to return (default " + McpRenderLimits.DEFAULT_USER_LIMIT
                        + ", max " + McpRenderLimits.MAX_USER_LIMIT + ")")
                .build();
    }

    @Override
    public McpToolResult call(JsonNode args, McpToolContext ctx) throws McpArgumentException {
        String filter = optString(args, "filter");
        int limit = optIntInRange(args, "limit", McpRenderLimits.DEFAULT_USER_LIMIT, 1, McpRenderLimits.MAX_USER_LIMIT);

        List<UserInfo> matches;
        if (filter == null || filter.isEmpty()) {
            matches = ctx.getUserInfoFacade().findAll();
        } else {
            UserInfo exact = ctx.getUserInfoFacade().findByUsername(filter);
            if (exact != null) {
                matches = Collections.singletonList(exact);
            } else {
                matches = substringFilter(ctx.getUserInfoFacade().findAll(), filter);
            }
        }

        return McpToolResult.text(render(filter, matches, limit));
    }

    private List<UserInfo> substringFilter(List<UserInfo> all, String filter) {
        String needle = filter.toLowerCase(Locale.ROOT);
        List<UserInfo> result = new ArrayList<>();
        for (UserInfo u : all) {
            if (contains(u.getUsername(), needle) || contains(u.getFirstName(), needle) || contains(u.getLastName(), needle)) {
                result.add(u);
            }
        }
        return result;
    }

    private boolean contains(String value, String needle) {
        return value != null && value.toLowerCase(Locale.ROOT).contains(needle);
    }

    private String render(String filter, List<UserInfo> matches, int limit) {
        StringBuilder sb = new StringBuilder();
        sb.append("Users").append(filter == null || filter.isEmpty() ? "" : " matching \"" + filter + "\"")
                .append(" (").append(matches.size()).append(")\n");

        int shown = Math.min(limit, matches.size());
        for (int i = 0; i < shown; i++) {
            UserInfo u = matches.get(i);
            sb.append("- id=").append(u.getId())
                    .append(" | ").append(nz(u.getUsername()))
                    .append(" | ").append(nz(u.getFirstName())).append(" ").append(nz(u.getLastName()))
                    .append("\n");
        }
        if (matches.size() > shown) {
            sb.append("… showing ").append(shown).append(" of ").append(matches.size())
                    .append("; increase limit (max ").append(McpRenderLimits.MAX_USER_LIMIT).append(") or narrow filter\n");
        }

        return sb.toString();
    }
}
