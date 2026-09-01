/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

/** Shared constants for the MCP endpoint: private ObjectMapper, header names, error codes, server identity. */
public final class McpConstants {

    private McpConstants() {
    }

    public static final ObjectMapper MAPPER = new ObjectMapper();

    public static final String PROTOCOL_VERSION = "2026-07-28";
    public static final List<String> SUPPORTED_PROTOCOL_VERSIONS = Collections.singletonList(PROTOCOL_VERSION);

    // Legacy (pre-2026-07-28) revisions served via a sessionless "initialize" handshake; see McpRoute#initializeLegacy.
    public static final List<String> LEGACY_PROTOCOL_VERSIONS = Arrays.asList("2025-11-25", "2025-06-18", "2025-03-26");
    public static final String LEGACY_PROTOCOL_VERSION_DEFAULT = "2025-11-25";

    public static final String HEADER_PROTOCOL_VERSION = "MCP-Protocol-Version";
    public static final String HEADER_METHOD = "Mcp-Method";
    public static final String HEADER_NAME = "Mcp-Name";
    public static final String HEADER_ORIGIN = "Origin";
    public static final String HEADER_TOKEN = "token";

    public static final String META_PROTOCOL_VERSION = "io.modelcontextprotocol/protocolVersion";
    public static final String META_CLIENT_INFO = "io.modelcontextprotocol/clientInfo";
    public static final String META_CLIENT_CAPABILITIES = "io.modelcontextprotocol/clientCapabilities";
    public static final String META_SERVER_INFO = "io.modelcontextprotocol/serverInfo";

    public static final int ERR_PARSE_ERROR = -32700;
    public static final int ERR_INVALID_REQUEST = -32600;
    public static final int ERR_METHOD_NOT_FOUND = -32601;
    public static final int ERR_INVALID_PARAMS = -32602;
    public static final int ERR_INTERNAL_ERROR = -32603;
    public static final int ERR_UNAUTHORIZED = -32001;
    public static final int ERR_HEADER_MISMATCH = -32020;
    public static final int ERR_UNSUPPORTED_VERSION = -32022;

    public static final String SERVER_NAME = "bely";
    public static final String SERVER_TITLE = "BELY Electronic Logbook";
    public static final String SERVER_VERSION = "1.0.0";

    public static final String INSTRUCTIONS =
            "BELY (Best Electronic Logbook Yet) is an electronic logbook. A \"log document\" "
            + "(sometimes just \"document\") is a dated container such as an operations shift log; "
            + "each document belongs to a logbook type (e.g. \"Ops Shift\") and a system (e.g. "
            + "\"Storage Ring\"). A document may have \"sections\" — sub-documents that group their "
            + "own log entries under a heading within the parent document. A \"log entry\" (or "
            + "\"log\") is one timestamped note inside a document or section, and may have replies "
            + "and reactions. Use bely_list_lookups to discover valid logbook type and system ids "
            + "before filtering searches or listings by them. Use bely_search to find documents or "
            + "entries by text; use bely_get_log_document / bely_get_log_entry to read one in full "
            + "once you know its id. All tools are read-only.";

    public static final String PROP_ENABLED = "cdb.portal.mcp.enabled";
    // Defaults to false by design: all MCP tools are read-only and the equivalent REST reads are unauthenticated too. Set true to require a valid token header.
    public static final String PROP_REQUIRE_AUTH = "cdb.portal.mcp.requireAuth";
    public static final String PROP_ALLOWED_ORIGINS = "cdb.portal.mcp.allowedOrigins";
}
