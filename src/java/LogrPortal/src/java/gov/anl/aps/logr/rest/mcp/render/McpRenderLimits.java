/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp.render;

/** Every numeric cap applied when rendering MCP tool output, collected in one place for easy tuning. */
public final class McpRenderLimits {

    private McpRenderLimits() {
    }

    public static final int MAX_RESULT_CHARS = 40000;

    public static final int DEFAULT_ROW_LIMIT = 25;
    public static final int MAX_ROW_LIMIT = 200;

    public static final int DEFAULT_ENTRY_LIMIT = 20;
    public static final int MAX_ENTRY_LIMIT = 100;

    public static final int DEFAULT_ENTRY_BODY_CHARS = 1500;
    public static final int MAX_ENTRY_BODY_CHARS = 20000;

    public static final int MAX_SINGLE_ENTRY_CHARS = 50000;
    public static final int SEARCH_SNIPPET_CHARS = 300;

    public static final int DEFAULT_USER_LIMIT = 100;
    public static final int MAX_USER_LIMIT = 500;
}
