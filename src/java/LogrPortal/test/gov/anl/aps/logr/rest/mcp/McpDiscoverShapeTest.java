/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

/** Regression guard for the {@code server/discover} shape bug: {@link McpRoute#discover} must match the spec's {@code DiscoverResult}. */
public class McpDiscoverShapeTest {

    public static void main(String[] args) throws Exception {
        int passed = 0;
        int failed = 0;
        for (java.lang.reflect.Method m : McpDiscoverShapeTest.class.getDeclaredMethods()) {
            if (m.getName().startsWith("test") && m.getParameterCount() == 0) {
                try {
                    m.setAccessible(true);
                    m.invoke(null);
                    System.out.println("PASS " + m.getName());
                    passed++;
                } catch (java.lang.reflect.InvocationTargetException e) {
                    System.out.println("FAIL " + m.getName() + ": " + e.getCause());
                    failed++;
                }
            }
        }
        System.out.println(passed + " passed, " + failed + " failed");
        if (failed > 0) {
            System.exit(1);
        }
    }

    static void check(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }

    static void testSupportedVersionsIsNonEmptyAndContainsProtocolVersion() {
        ObjectNode result = new McpRoute().discover();
        JsonNode supported = result.get("supportedVersions");
        check(supported != null && supported.isArray() && supported.size() > 0,
                "supportedVersions must be a non-empty array");
        boolean containsCurrent = false;
        for (JsonNode v : supported) {
            if (McpConstants.PROTOCOL_VERSION.equals(v.asText())) {
                containsCurrent = true;
            }
        }
        check(containsCurrent, "supportedVersions must contain " + McpConstants.PROTOCOL_VERSION);
    }

    static void testDoesNotUseTheOldFieldName() {
        ObjectNode result = new McpRoute().discover();
        check(!result.has("supportedProtocolVersions"),
                "the old, spec-incorrect field name must not be present");
    }

    static void testResultTypeIsComplete() {
        ObjectNode result = new McpRoute().discover();
        check("complete".equals(result.path("resultType").asText()), "resultType must be \"complete\"");
    }

    static void testHasCapabilities() {
        ObjectNode result = new McpRoute().discover();
        check(result.has("capabilities"), "discover() result must have capabilities");
        check(result.path("capabilities").has("tools"), "capabilities must advertise tools");
    }

    static void testMetaServerInfoNameIsPresent() {
        ObjectNode result = new McpRoute().discover();
        JsonNode metaServerInfo = result.path("_meta").path(McpConstants.META_SERVER_INFO);
        check(McpConstants.SERVER_NAME.equals(metaServerInfo.path("name").asText()),
                "_meta[\"" + McpConstants.META_SERVER_INFO + "\"].name must be \"" + McpConstants.SERVER_NAME + "\"");
    }
}
