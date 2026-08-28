/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp.protocol;

import com.fasterxml.jackson.databind.JsonNode;

/** A transport/protocol-level failure: carries the HTTP status plus the JSON-RPC error to embed in the body. */
public class McpProtocolException extends Exception {

    private final int httpStatus;
    private final int jsonRpcCode;
    private final JsonNode data;

    public McpProtocolException(int httpStatus, int jsonRpcCode, String message) {
        this(httpStatus, jsonRpcCode, message, null);
    }

    public McpProtocolException(int httpStatus, int jsonRpcCode, String message, JsonNode data) {
        super(message);
        this.httpStatus = httpStatus;
        this.jsonRpcCode = jsonRpcCode;
        this.data = data;
    }

    public int getHttpStatus() {
        return httpStatus;
    }

    public int getJsonRpcCode() {
        return jsonRpcCode;
    }

    public JsonNode getData() {
        return data;
    }

    public JsonRpcError toJsonRpcError() {
        return new JsonRpcError(jsonRpcCode, getMessage(), data);
    }
}
