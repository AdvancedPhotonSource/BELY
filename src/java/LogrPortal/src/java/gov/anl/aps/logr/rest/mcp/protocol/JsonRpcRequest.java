/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp.protocol;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.MissingNode;
import gov.anl.aps.logr.rest.mcp.McpConstants;

/** Inbound JSON-RPC 2.0 envelope; {@link #parse} assumes malformed-JSON bodies were already rejected by the caller. */
public class JsonRpcRequest {

    private final JsonNode id;
    private final String method;
    private final JsonNode params;

    private JsonRpcRequest(JsonNode id, String method, JsonNode params) {
        this.id = id;
        this.method = method;
        this.params = params;
    }

    public static JsonRpcRequest parse(JsonNode root) throws McpProtocolException {
        if (root == null || root.isMissingNode() || root.isNull()) {
            throw new McpProtocolException(400, McpConstants.ERR_INVALID_REQUEST, "Empty request body");
        }
        if (root.isArray()) {
            throw new McpProtocolException(400, McpConstants.ERR_INVALID_REQUEST, "Batching is not supported");
        }
        if (!root.isObject()) {
            throw new McpProtocolException(400, McpConstants.ERR_INVALID_REQUEST, "Request must be a JSON object");
        }

        JsonNode jsonrpc = root.get("jsonrpc");
        if (jsonrpc == null || !"2.0".equals(jsonrpc.asText())) {
            throw new McpProtocolException(400, McpConstants.ERR_INVALID_REQUEST, "Missing or invalid \"jsonrpc\" version, expected \"2.0\"");
        }

        JsonNode methodNode = root.get("method");
        if (methodNode == null || !methodNode.isTextual() || methodNode.asText().isEmpty()) {
            throw new McpProtocolException(400, McpConstants.ERR_INVALID_REQUEST, "Missing \"method\"");
        }

        JsonNode idNode = root.has("id") ? root.get("id") : MissingNode.getInstance();
        JsonNode paramsNode = root.has("params") ? root.get("params") : MissingNode.getInstance();

        return new JsonRpcRequest(idNode, methodNode.asText(), paramsNode);
    }

    public JsonNode getId() {
        return id;
    }

    public boolean hasId() {
        return id != null && !id.isMissingNode();
    }

    public String getMethod() {
        return method;
    }

    public JsonNode getParams() {
        return params;
    }
}
