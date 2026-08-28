/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import gov.anl.aps.logr.rest.mcp.protocol.JsonRpcRequest;

/** Checks {@link McpRoute#initializeLegacy}, the sessionless legacy {@code initialize} handshake for pre-2026-07-28 clients. */
public class McpInitializeLegacyTest {

    public static void main(String[] args) throws Exception {
        int passed = 0;
        int failed = 0;
        for (java.lang.reflect.Method m : McpInitializeLegacyTest.class.getDeclaredMethods()) {
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

    private static JsonRpcRequest initializeRequest(String protocolVersion) throws Exception {
        StringBuilder json = new StringBuilder();
        json.append("{\"jsonrpc\":\"2.0\",\"id\":0,\"method\":\"initialize\",\"params\":{");
        if (protocolVersion != null) {
            json.append("\"protocolVersion\":\"").append(protocolVersion).append("\",");
        }
        json.append("\"capabilities\":{},\"clientInfo\":{\"name\":\"x\",\"version\":\"1\"}}}");
        JsonNode root = McpConstants.MAPPER.readTree(json.toString());
        return JsonRpcRequest.parse(root);
    }

    static void testSupportedLegacyVersionIsEchoedBack() throws Exception {
        String requested = "2025-06-18";
        ObjectNode result = new McpRoute().initializeLegacy(initializeRequest(requested));
        check(requested.equals(result.path("protocolVersion").asText()),
                "a supported legacy version must be echoed back unchanged");
    }

    static void testUnrecognizedVersionFallsBackToDefault() throws Exception {
        ObjectNode result = new McpRoute().initializeLegacy(initializeRequest("1900-01-01"));
        check(McpConstants.LEGACY_PROTOCOL_VERSION_DEFAULT.equals(result.path("protocolVersion").asText()),
                "an unrecognized version must fall back to " + McpConstants.LEGACY_PROTOCOL_VERSION_DEFAULT);
    }

    static void testMissingProtocolVersionFallsBackToDefault() throws Exception {
        ObjectNode result = new McpRoute().initializeLegacy(initializeRequest(null));
        check(McpConstants.LEGACY_PROTOCOL_VERSION_DEFAULT.equals(result.path("protocolVersion").asText()),
                "a missing protocolVersion must fall back to " + McpConstants.LEGACY_PROTOCOL_VERSION_DEFAULT);
    }

    static void testResultShapeMatchesLegacyInitializeResult() throws Exception {
        ObjectNode result = new McpRoute().initializeLegacy(initializeRequest(McpConstants.LEGACY_PROTOCOL_VERSION_DEFAULT));
        check(result.path("capabilities").has("tools"), "capabilities.tools must be present");
        check(McpConstants.SERVER_NAME.equals(result.path("serverInfo").path("name").asText()),
                "serverInfo.name must be \"" + McpConstants.SERVER_NAME + "\"");
        check(result.has("instructions"), "instructions must be present");
        check(!result.has("resultType"), "a legacy InitializeResult must not carry the modern-only \"resultType\" field");
        check(!result.has("_meta"), "a legacy InitializeResult must not carry modern-only \"_meta\"");
    }
}
