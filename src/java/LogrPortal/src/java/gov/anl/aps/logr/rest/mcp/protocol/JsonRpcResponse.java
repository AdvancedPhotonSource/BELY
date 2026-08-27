/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp.protocol;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import gov.anl.aps.logr.rest.mcp.McpConstants;

/** Builds outbound JSON-RPC 2.0 response envelopes as pre-serialized strings, bypassing the app-wide Jackson provider. */
public final class JsonRpcResponse {

    private JsonRpcResponse() {
    }

    public static String success(JsonNode id, JsonNode result) {
        ObjectNode node = McpConstants.MAPPER.createObjectNode();
        node.put("jsonrpc", "2.0");
        node.set("id", id);
        node.set("result", result);
        return node.toString();
    }

    public static String error(JsonNode id, JsonRpcError error) {
        ObjectNode node = McpConstants.MAPPER.createObjectNode();
        node.put("jsonrpc", "2.0");
        node.set("id", id == null || id.isMissingNode() ? McpConstants.MAPPER.nullNode() : id);
        node.set("error", error.toJson());
        return node.toString();
    }
}
