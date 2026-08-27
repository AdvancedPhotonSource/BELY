/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp.tools;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

/** One MCP tool: name/description/schema for {@code tools/list}, plus {@link #call} with a per-request context. */
public interface McpTool {

    String getName();

    String getTitle();

    String getDescription();

    ObjectNode getInputSchema();

    McpToolResult call(JsonNode args, McpToolContext ctx) throws McpArgumentException;
}
