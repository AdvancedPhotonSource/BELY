/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp.tools;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import gov.anl.aps.logr.rest.mcp.McpConstants;
import gov.anl.aps.logr.rest.mcp.render.McpTextRenderer;

/** The single text content block every MCP tool returns; {@code isError} marks a recoverable, retry-able failure. */
public class McpToolResult {

    private final String text;
    private final boolean isError;

    private McpToolResult(String text, boolean isError) {
        this.text = McpTextRenderer.capResult(text);
        this.isError = isError;
    }

    public static McpToolResult text(String text) {
        return new McpToolResult(text, false);
    }

    public static McpToolResult error(String message) {
        return new McpToolResult(message, true);
    }

    public ObjectNode toJson() {
        ObjectNode result = McpConstants.MAPPER.createObjectNode();
        ArrayNode content = result.putArray("content");
        ObjectNode block = content.addObject();
        block.put("type", "text");
        block.put("text", text);
        result.put("isError", isError);
        result.put("resultType", "complete");
        return result;
    }
}
