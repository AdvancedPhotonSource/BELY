/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp.render;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.TimeZone;
import java.util.function.Supplier;

/** Text-shaping helpers shared by every MCP tool renderer: truncation, whitespace collapsing, dates, lazy-load guard. */
public final class McpTextRenderer {

    private McpTextRenderer() {
    }

    public static String nz(String value) {
        return value == null ? "" : value;
    }

    public static String truncate(String text, int maxChars) {
        if (text == null) {
            return "";
        }
        if (text.length() <= maxChars) {
            return text;
        }
        return text.substring(0, maxChars);
    }

    public static String truncateWithMarker(String text, int maxChars, String followUpHint) {
        if (text == null) {
            return "";
        }
        if (text.length() <= maxChars) {
            return text;
        }
        return text.substring(0, maxChars)
                + "\n… [truncated " + (text.length() - maxChars) + " of " + text.length()
                + " chars; " + followUpHint + "]";
    }

    public static String collapseWhitespace(String text) {
        if (text == null) {
            return "";
        }
        return text.trim().replaceAll("\\s+", " ");
    }

    public static String isoDate(Date date) {
        if (date == null) {
            return "?";
        }
        SimpleDateFormat format = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'");
        format.setTimeZone(TimeZone.getTimeZone("UTC"));
        return format.format(date);
    }

    public static String safe(Supplier<String> supplier) {
        try {
            String value = supplier.get();
            return value == null ? "?" : value;
        } catch (RuntimeException e) {
            return "?";
        }
    }

    public static String capResult(String text) {
        if (text == null) {
            return "";
        }
        if (text.length() <= McpRenderLimits.MAX_RESULT_CHARS) {
            return text;
        }
        return text.substring(0, McpRenderLimits.MAX_RESULT_CHARS)
                + "\n… [result truncated at " + McpRenderLimits.MAX_RESULT_CHARS
                + " chars — narrow your query and try again]";
    }
}
