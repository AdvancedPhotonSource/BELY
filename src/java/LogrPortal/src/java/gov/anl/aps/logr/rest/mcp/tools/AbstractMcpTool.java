/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp.tools;

import com.fasterxml.jackson.databind.JsonNode;
import gov.anl.aps.logr.portal.model.db.entities.EntityType;
import gov.anl.aps.logr.portal.model.db.entities.ItemType;
import gov.anl.aps.logr.rest.entities.DateParam;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.stream.Collectors;
import javax.ws.rs.WebApplicationException;

/** Argument-extraction helpers shared by every tool; required accessors throw {@link McpArgumentException} (-32602). */
public abstract class AbstractMcpTool implements McpTool {

    protected static JsonNode arg(JsonNode args, String name) {
        if (args == null || !args.has(name) || args.get(name).isNull()) {
            return null;
        }
        return args.get(name);
    }

    protected static String optString(JsonNode args, String name) {
        JsonNode node = arg(args, name);
        return node == null ? null : node.asText();
    }

    protected static String reqString(JsonNode args, String name) throws McpArgumentException {
        String value = optString(args, name);
        if (value == null || value.isEmpty()) {
            throw new McpArgumentException("Missing required argument \"" + name + "\"");
        }
        return value;
    }

    protected static Integer optInteger(JsonNode args, String name) {
        JsonNode node = arg(args, name);
        return node == null ? null : node.asInt();
    }

    protected static int reqInteger(JsonNode args, String name) throws McpArgumentException {
        Integer value = optInteger(args, name);
        if (value == null) {
            throw new McpArgumentException("Missing required argument \"" + name + "\"");
        }
        return value;
    }

    protected static boolean optBoolean(JsonNode args, String name, boolean defaultValue) {
        JsonNode node = arg(args, name);
        return node == null ? defaultValue : node.asBoolean(defaultValue);
    }

    protected static int optIntInRange(JsonNode args, String name, int defaultValue, int min, int max) {
        Integer value = optInteger(args, name);
        if (value == null) {
            return defaultValue;
        }
        if (value < min) {
            return min;
        }
        if (value > max) {
            return max;
        }
        return value;
    }

    protected static List<Integer> optIntegerList(JsonNode args, String name) {
        List<Integer> result = new ArrayList<>();
        JsonNode node = arg(args, name);
        if (node != null && node.isArray()) {
            for (JsonNode item : node) {
                result.add(item.asInt());
            }
        }
        return result;
    }

    protected static Date optDate(JsonNode args, String name) throws McpArgumentException {
        String value = optString(args, name);
        if (value == null || value.isEmpty()) {
            return null;
        }
        try {
            return new DateParam(value).getDate();
        } catch (WebApplicationException e) {
            throw new McpArgumentException("Invalid date for \"" + name + "\": \"" + value
                    + "\" (expected ISO 8601, \"yyyy-MM-dd HH:mm:ss\", or \"yyyy-MM-dd\")");
        }
    }

    protected static String describeEntityTypes(List<EntityType> types) {
        return types.stream()
                .map(t -> t.getId() + " (" + t.getName() + ")")
                .collect(Collectors.joining(", "));
    }

    protected static String describeItemTypes(List<ItemType> types) {
        return types.stream()
                .map(t -> t.getId() + " (" + t.getName() + ")")
                .collect(Collectors.joining(", "));
    }
}
