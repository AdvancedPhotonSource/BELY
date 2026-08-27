/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp.tools.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import gov.anl.aps.logr.common.mqtt.constants.CallSource;
import gov.anl.aps.logr.common.mqtt.model.entities.LogbookSearchOptions;
import gov.anl.aps.logr.portal.controllers.utilities.ItemDomainLogbookControllerUtility;
import gov.anl.aps.logr.portal.controllers.utilities.SearchControllerUtility;
import gov.anl.aps.logr.portal.model.db.entities.EntityType;
import gov.anl.aps.logr.portal.model.db.entities.ItemType;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
import gov.anl.aps.logr.portal.utilities.SearchResult;
import gov.anl.aps.logr.rest.mcp.render.McpRenderLimits;
import gov.anl.aps.logr.rest.mcp.schema.JsonSchemaBuilder;
import gov.anl.aps.logr.rest.mcp.tools.AbstractMcpTool;
import gov.anl.aps.logr.rest.mcp.tools.McpArgumentException;
import gov.anl.aps.logr.rest.mcp.tools.McpToolContext;
import gov.anl.aps.logr.rest.mcp.tools.McpToolResult;
import java.util.ArrayList;
import java.util.Date;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;

import static gov.anl.aps.logr.rest.mcp.render.McpTextRenderer.collapseWhitespace;
import static gov.anl.aps.logr.rest.mcp.render.McpTextRenderer.isoDate;
import static gov.anl.aps.logr.rest.mcp.render.McpTextRenderer.nz;
import static gov.anl.aps.logr.rest.mcp.render.McpTextRenderer.truncate;

/** Searches log documents and entries by text, reusing {@code SearchRoute}'s utility calls, tagged {@link CallSource#MCP}. */
public class BelySearchTool extends AbstractMcpTool {

    @Override
    public String getName() {
        return "bely_search";
    }

    @Override
    public String getTitle() {
        return "Search BELY";
    }

    @Override
    public String getDescription() {
        return "Search log documents and log entries by text, optionally filtered by logbook type, "
                + "system, user, and date ranges. Returns the top matches with enough detail to pick "
                + "a document or entry to fetch in full with bely_get_log_document / bely_get_log_entry.";
    }

    @Override
    public ObjectNode getInputSchema() {
        return new JsonSchemaBuilder()
                .requiredStringProp("searchText", "Search text; supports ? (single char) and * (multiple chars) wildcards")
                .booleanProp("caseInsensitive", "Use case-insensitive matching (default true)")
                .integerArrayProp("logbookTypeIds", "Restrict to these logbook type ids (see bely_list_lookups kind=logbookTypes)")
                .integerArrayProp("systemIds", "Restrict to these system ids (see bely_list_lookups kind=systems)")
                .integerArrayProp("userIds", "Restrict to entries entered by these user ids")
                .stringProp("startModifiedDate", "ISO 8601 or yyyy-MM-dd start of last-modified date range")
                .stringProp("endModifiedDate", "ISO 8601 or yyyy-MM-dd end of last-modified date range")
                .stringProp("startCreatedDate", "ISO 8601 or yyyy-MM-dd start of created date range")
                .stringProp("endCreatedDate", "ISO 8601 or yyyy-MM-dd end of created date range")
                .integerProp("limit", "Maximum rows per result group (default " + McpRenderLimits.DEFAULT_ROW_LIMIT
                        + ", max " + McpRenderLimits.MAX_ROW_LIMIT + ")")
                .build();
    }

    @Override
    public McpToolResult call(JsonNode args, McpToolContext ctx) throws McpArgumentException {
        String searchText = reqString(args, "searchText");
        boolean caseInsensitive = optBoolean(args, "caseInsensitive", true);
        int limit = optIntInRange(args, "limit", McpRenderLimits.DEFAULT_ROW_LIMIT, 1, McpRenderLimits.MAX_ROW_LIMIT);

        List<EntityType> entityTypeList;
        List<ItemType> itemTypeList;
        List<UserInfo> userList;
        Date startModifiedTime;
        Date endModifiedTime;
        Date startCreatedTime;
        Date endCreatedTime;
        try {
            entityTypeList = resolveEntityTypes(ctx, optIntegerList(args, "logbookTypeIds"));
            itemTypeList = resolveItemTypes(ctx, optIntegerList(args, "systemIds"));
            userList = resolveUsers(ctx, optIntegerList(args, "userIds"));
            startModifiedTime = optDate(args, "startModifiedDate");
            endModifiedTime = ItemDomainLogbookControllerUtility.adjustEndTimeForSearch(optDate(args, "endModifiedDate"));
            startCreatedTime = optDate(args, "startCreatedDate");
            endCreatedTime = ItemDomainLogbookControllerUtility.adjustEndTimeForSearch(optDate(args, "endCreatedDate"));
        } catch (McpArgumentException e) {
            return McpToolResult.error(e.getMessage());
        }

        ItemDomainLogbookControllerUtility utility = new ItemDomainLogbookControllerUtility();
        Map searchArgs = utility.createAdvancedSearchMap(
                entityTypeList, itemTypeList, userList,
                startModifiedTime, endModifiedTime,
                startCreatedTime, endCreatedTime);

        LinkedList<SearchResult> documentResults = utility.performEntitySearch(searchText, searchArgs, caseInsensitive);
        LinkedList<SearchResult> logEntryResults = utility.searchLogEntries(searchText, caseInsensitive, searchArgs);

        LogbookSearchOptions searchOptions = new LogbookSearchOptions(
                entityTypeList, itemTypeList, userList,
                startModifiedTime, endModifiedTime,
                startCreatedTime, endCreatedTime, caseInsensitive);
        SearchControllerUtility.publishSearchMqttEvent(searchText, searchOptions, CallSource.MCP);

        return McpToolResult.text(render(searchText, documentResults, logEntryResults, limit));
    }

    private List<EntityType> resolveEntityTypes(McpToolContext ctx, List<Integer> ids) throws McpArgumentException {
        List<EntityType> resolved = new ArrayList<>();
        if (ids.isEmpty()) {
            return resolved;
        }
        List<EntityType> available = ctx.getLogbookTypes();
        for (Integer id : ids) {
            EntityType match = available.stream().filter(t -> t.getId().equals(id)).findFirst().orElse(null);
            if (match == null) {
                throw new McpArgumentException("Unknown logbookTypeId " + id + ". Valid ids: " + describeEntityTypes(available));
            }
            resolved.add(match);
        }
        return resolved;
    }

    private List<ItemType> resolveItemTypes(McpToolContext ctx, List<Integer> ids) throws McpArgumentException {
        List<ItemType> resolved = new ArrayList<>();
        if (ids.isEmpty()) {
            return resolved;
        }
        List<ItemType> available = ctx.getLogbookSystems();
        for (Integer id : ids) {
            ItemType match = available.stream().filter(t -> t.getId().equals(id)).findFirst().orElse(null);
            if (match == null) {
                throw new McpArgumentException("Unknown systemId " + id + ". Valid ids: " + describeItemTypes(available));
            }
            resolved.add(match);
        }
        return resolved;
    }

    private List<UserInfo> resolveUsers(McpToolContext ctx, List<Integer> ids) throws McpArgumentException {
        List<UserInfo> resolved = new ArrayList<>();
        for (Integer id : ids) {
            UserInfo match = ctx.getUserInfoFacade().findById(id);
            if (match == null) {
                throw new McpArgumentException("Unknown userId " + id + ". Use bely_list_users to find valid ids.");
            }
            resolved.add(match);
        }
        return resolved;
    }

    private String render(String searchText, List<SearchResult> documentResults, List<SearchResult> logEntryResults, int limit) {
        StringBuilder sb = new StringBuilder();
        sb.append("Search results for \"").append(searchText).append("\"\n\n");

        sb.append("Log documents (").append(documentResults.size()).append(" match")
                .append(documentResults.size() == 1 ? "" : "es").append(")\n");
        int shown = Math.min(limit, documentResults.size());
        for (int i = 0; i < shown; i++) {
            SearchResult r = documentResults.get(i);
            sb.append("- logDocumentId=").append(r.getLogDocumentId())
                    .append(" | ").append(nz(r.getObjectName()))
                    .append(" | ").append(nz(r.getLogbookType()))
                    .append(" / ").append(nz(r.getSystem()))
                    .append(" | modified ").append(isoDate(r.getLastModifiedOn()))
                    .append("\n");
        }
        if (documentResults.size() > shown) {
            sb.append("… showing ").append(shown).append(" of ").append(documentResults.size())
                    .append(" document matches; increase limit (max ").append(McpRenderLimits.MAX_ROW_LIMIT)
                    .append(") or narrow filters to see more\n");
        }

        sb.append("\nLog entries (").append(logEntryResults.size()).append(" match")
                .append(logEntryResults.size() == 1 ? "" : "es").append(")\n");
        shown = Math.min(limit, logEntryResults.size());
        for (int i = 0; i < shown; i++) {
            SearchResult r = logEntryResults.get(i);
            sb.append("- logDocumentId=").append(r.getLogDocumentId())
                    .append(" logId=").append(r.getLogEntryId())
                    .append(" | ").append(truncate(collapseWhitespace(r.getDisplay()), McpRenderLimits.SEARCH_SNIPPET_CHARS))
                    .append(" | modified ").append(isoDate(r.getLastModifiedOn()))
                    .append("\n");
        }
        if (logEntryResults.size() > shown) {
            sb.append("… showing ").append(shown).append(" of ").append(logEntryResults.size())
                    .append(" entry matches; call bely_get_log_entry with a specific logDocumentId/logId, ")
                    .append("narrow filters, or increase limit (max ").append(McpRenderLimits.MAX_ROW_LIMIT).append(")\n");
        }

        return sb.toString();
    }
}
