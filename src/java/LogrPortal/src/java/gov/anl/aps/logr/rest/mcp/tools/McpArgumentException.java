/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp.tools;

/** Missing/malformed tool argument; the route maps this to JSON-RPC -32602, distinct from an {@code isError} result. */
public class McpArgumentException extends Exception {

    public McpArgumentException(String message) {
        super(message);
    }
}
