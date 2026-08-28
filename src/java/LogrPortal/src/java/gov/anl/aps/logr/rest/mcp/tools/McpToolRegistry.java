/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp.tools;

import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.Map;

/** Registered MCP tools in a deterministic order — a spec SHOULD for {@code tools/list}. */
public class McpToolRegistry {

    private final Map<String, McpTool> tools = new LinkedHashMap<>();

    public void register(McpTool tool) {
        tools.put(tool.getName(), tool);
    }

    public McpTool get(String name) {
        return tools.get(name);
    }

    public Collection<McpTool> list() {
        return tools.values();
    }
}
