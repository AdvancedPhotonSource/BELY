/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp.schema;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import gov.anl.aps.logr.rest.mcp.McpConstants;

/** Fluent builder for the small subset of JSON Schema needed to describe MCP tool input — not general-purpose. */
public class JsonSchemaBuilder {

    private final ObjectNode schema;
    private final ObjectNode properties;
    private final ArrayNode required;

    public JsonSchemaBuilder() {
        schema = McpConstants.MAPPER.createObjectNode();
        schema.put("type", "object");
        properties = schema.putObject("properties");
        required = schema.putArray("required");
    }

    public JsonSchemaBuilder stringProp(String name, String description) {
        return prop(name, "string", description, false);
    }

    public JsonSchemaBuilder requiredStringProp(String name, String description) {
        return prop(name, "string", description, true);
    }

    public JsonSchemaBuilder integerProp(String name, String description) {
        return prop(name, "integer", description, false);
    }

    public JsonSchemaBuilder requiredIntegerProp(String name, String description) {
        return prop(name, "integer", description, true);
    }

    public JsonSchemaBuilder booleanProp(String name, String description) {
        return prop(name, "boolean", description, false);
    }

    public JsonSchemaBuilder integerArrayProp(String name, String description) {
        ObjectNode p = properties.putObject(name);
        p.put("type", "array");
        p.putObject("items").put("type", "integer");
        if (description != null) {
            p.put("description", description);
        }
        return this;
    }

    public JsonSchemaBuilder enumProp(String name, String description, String... values) {
        ObjectNode p = properties.putObject(name);
        p.put("type", "string");
        if (description != null) {
            p.put("description", description);
        }
        ArrayNode enumNode = p.putArray("enum");
        for (String value : values) {
            enumNode.add(value);
        }
        return this;
    }

    public JsonSchemaBuilder requiredEnumProp(String name, String description, String... values) {
        enumProp(name, description, values);
        required.add(name);
        return this;
    }

    private JsonSchemaBuilder prop(String name, String type, String description, boolean isRequired) {
        ObjectNode p = properties.putObject(name);
        p.put("type", type);
        if (description != null) {
            p.put("description", description);
        }
        if (isRequired) {
            required.add(name);
        }
        return this;
    }

    public ObjectNode build() {
        if (required.isEmpty()) {
            schema.remove("required");
        }
        return schema;
    }
}
