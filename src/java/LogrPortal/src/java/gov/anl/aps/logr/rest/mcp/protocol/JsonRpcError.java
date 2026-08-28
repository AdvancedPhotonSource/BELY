/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp.protocol;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import gov.anl.aps.logr.rest.mcp.McpConstants;

/** JSON-RPC 2.0 error object: {@code { code, message, data? }}. */
public class JsonRpcError {

    private final int code;
    private final String message;
    private final JsonNode data;

    public JsonRpcError(int code, String message) {
        this(code, message, null);
    }

    public JsonRpcError(int code, String message, JsonNode data) {
        this.code = code;
        this.message = message;
        this.data = data;
    }

    public int getCode() {
        return code;
    }

    public ObjectNode toJson() {
        ObjectNode node = McpConstants.MAPPER.createObjectNode();
        node.put("code", code);
        node.put("message", message);
        if (data != null) {
            node.set("data", data);
        }
        return node;
    }
}
