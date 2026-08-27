/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp;

import com.fasterxml.jackson.databind.JsonNode;
import gov.anl.aps.logr.rest.mcp.protocol.JsonRpcRequest;
import gov.anl.aps.logr.rest.mcp.protocol.McpProtocolException;
import java.util.Base64;
import java.util.Collections;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import javax.ws.rs.core.Cookie;
import javax.ws.rs.core.HttpHeaders;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.MultivaluedHashMap;
import javax.ws.rs.core.MultivaluedMap;

/** Matrix test for {@link McpRoute#validateHeaders}, run outside a container via the {@link FakeHttpHeaders} stub. */
public class McpRouteHeaderValidationTest {

    private static final String V = McpConstants.PROTOCOL_VERSION;

    public static void main(String[] args) throws Exception {
        int passed = 0;
        int failed = 0;
        for (java.lang.reflect.Method m : McpRouteHeaderValidationTest.class.getDeclaredMethods()) {
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

    private static JsonRpcRequest request(String method, String metaVersion, String name) throws Exception {
        StringBuilder json = new StringBuilder();
        json.append("{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"").append(method).append("\",\"params\":{");
        if (metaVersion != null) {
            json.append("\"_meta\":{\"").append(McpConstants.META_PROTOCOL_VERSION).append("\":\"").append(metaVersion).append("\"},");
        }
        if (name != null) {
            json.append("\"name\":\"").append(name).append("\",");
        }
        json.append("\"arguments\":{}}}");
        JsonNode root = McpConstants.MAPPER.readTree(json.toString());
        return JsonRpcRequest.parse(root);
    }

    private static McpProtocolException expectThrow(JsonRpcRequest request, HttpHeaders headers) {
        try {
            new McpRoute().validateHeaders(request, headers);
        } catch (McpProtocolException e) {
            return e;
        }
        throw new AssertionError("expected validateHeaders to throw for " + request.getMethod());
    }

    static void testWellFormedModernRequestPasses() throws Exception {
        JsonRpcRequest req = request("server/discover", V, null);
        FakeHttpHeaders headers = new FakeHttpHeaders()
                .with(McpConstants.HEADER_METHOD, "server/discover")
                .with(McpConstants.HEADER_PROTOCOL_VERSION, V);
        new McpRoute().validateHeaders(req, headers); // must not throw
    }

    static void testMissingMcpMethodHeaderIsHeaderMismatch() throws Exception {
        JsonRpcRequest req = request("tools/list", V, null);
        FakeHttpHeaders headers = new FakeHttpHeaders().with(McpConstants.HEADER_PROTOCOL_VERSION, V);
        McpProtocolException e = expectThrow(req, headers);
        check(e.getJsonRpcCode() == McpConstants.ERR_HEADER_MISMATCH, "missing Mcp-Method must be -32020, got " + e.getJsonRpcCode());
        check(e.getHttpStatus() == 400, "must be HTTP 400");
    }

    static void testMcpMethodHeaderMismatchedAgainstBodyMethod() throws Exception {
        JsonRpcRequest req = request("tools/call", V, "bely_search");
        FakeHttpHeaders headers = new FakeHttpHeaders()
                .with(McpConstants.HEADER_METHOD, "tools/list") // wrong on purpose
                .with(McpConstants.HEADER_PROTOCOL_VERSION, V)
                .with(McpConstants.HEADER_NAME, "bely_search");
        McpProtocolException e = expectThrow(req, headers);
        check(e.getJsonRpcCode() == McpConstants.ERR_HEADER_MISMATCH, "Mcp-Method mismatch must be -32020");
    }

    static void testMissingMetaProtocolVersionIsLegacyDiagnostic() throws Exception {
        JsonRpcRequest req = request("server/discover", null, null);
        FakeHttpHeaders headers = new FakeHttpHeaders().with(McpConstants.HEADER_METHOD, "server/discover");
        McpProtocolException e = expectThrow(req, headers);
        check(e.getJsonRpcCode() == McpConstants.ERR_UNSUPPORTED_VERSION, "missing _meta protocolVersion must be -32022, got " + e.getJsonRpcCode());
        check(e.getMessage().contains(V), "the diagnostic must name the supported version so a legacy client can show it");
    }

    static void testProtocolVersionHeaderMissingIsHeaderMismatch() throws Exception {
        JsonRpcRequest req = request("server/discover", V, null);
        FakeHttpHeaders headers = new FakeHttpHeaders().with(McpConstants.HEADER_METHOD, "server/discover");
        McpProtocolException e = expectThrow(req, headers);
        check(e.getJsonRpcCode() == McpConstants.ERR_HEADER_MISMATCH, "missing MCP-Protocol-Version header must be -32020");
    }

    static void testProtocolVersionHeaderDisagreesWithMeta() throws Exception {
        JsonRpcRequest req = request("server/discover", V, null);
        FakeHttpHeaders headers = new FakeHttpHeaders()
                .with(McpConstants.HEADER_METHOD, "server/discover")
                .with(McpConstants.HEADER_PROTOCOL_VERSION, "2025-06-18"); // disagrees with body's _meta
        McpProtocolException e = expectThrow(req, headers);
        check(e.getJsonRpcCode() == McpConstants.ERR_HEADER_MISMATCH, "header/body protocol version disagreement must be -32020, not -32022");
    }

    static void testUnsupportedButMirroredVersionIsUnsupportedVersion() throws Exception {
        JsonRpcRequest req = request("server/discover", "1900-01-01", null);
        FakeHttpHeaders headers = new FakeHttpHeaders()
                .with(McpConstants.HEADER_METHOD, "server/discover")
                .with(McpConstants.HEADER_PROTOCOL_VERSION, "1900-01-01"); // agrees with body, but nobody supports this
        McpProtocolException e = expectThrow(req, headers);
        check(e.getJsonRpcCode() == McpConstants.ERR_UNSUPPORTED_VERSION, "mirrored-but-unsupported version must be -32022");
        check(e.getData() != null && e.getData().get("requested").asText().equals("1900-01-01"), "data.requested must echo the bad version");
        check(e.getData().get("supported").isArray(), "data.supported must list what we do support");
    }

    static void testToolsCallWithMismatchedMcpNameHeader() throws Exception {
        JsonRpcRequest req = request("tools/call", V, "bely_search");
        FakeHttpHeaders headers = new FakeHttpHeaders()
                .with(McpConstants.HEADER_METHOD, "tools/call")
                .with(McpConstants.HEADER_PROTOCOL_VERSION, V)
                .with(McpConstants.HEADER_NAME, "bely_list_users"); // does not match params.name
        McpProtocolException e = expectThrow(req, headers);
        check(e.getJsonRpcCode() == McpConstants.ERR_HEADER_MISMATCH, "Mcp-Name mismatch must be -32020");
    }

    static void testToolsCallWithBase64WrappedMcpNameMatching() throws Exception {
        JsonRpcRequest req = request("tools/call", V, "bely_search");
        String wrapped = "=?base64?" + Base64.getEncoder().encodeToString("bely_search".getBytes("UTF-8")) + "?=";
        FakeHttpHeaders headers = new FakeHttpHeaders()
                .with(McpConstants.HEADER_METHOD, "tools/call")
                .with(McpConstants.HEADER_PROTOCOL_VERSION, V)
                .with(McpConstants.HEADER_NAME, wrapped);
        new McpRoute().validateHeaders(req, headers); // must not throw
    }

    static void testNonToolsCallMethodIgnoresMcpNameHeader() throws Exception {
        JsonRpcRequest req = request("tools/list", V, null);
        FakeHttpHeaders headers = new FakeHttpHeaders()
                .with(McpConstants.HEADER_METHOD, "tools/list")
                .with(McpConstants.HEADER_PROTOCOL_VERSION, V);
        new McpRoute().validateHeaders(req, headers); // must not throw: Mcp-Name is only checked for tools/call
    }

    // Minimal HttpHeaders stub — validateHeaders only ever calls getHeaderString; every other method is unused.
    private static class FakeHttpHeaders implements HttpHeaders {

        private final Map<String, String> headers = new HashMap<>();

        FakeHttpHeaders with(String name, String value) {
            headers.put(name, value);
            return this;
        }

        @Override
        public String getHeaderString(String name) {
            return headers.get(name);
        }

        @Override
        public List<String> getRequestHeader(String name) {
            String value = headers.get(name);
            return value == null ? Collections.emptyList() : Collections.singletonList(value);
        }

        @Override
        public MultivaluedMap<String, String> getRequestHeaders() {
            MultivaluedMap<String, String> map = new MultivaluedHashMap<>();
            headers.forEach(map::add);
            return map;
        }

        @Override
        public List<MediaType> getAcceptableMediaTypes() {
            return Collections.emptyList();
        }

        @Override
        public List<Locale> getAcceptableLanguages() {
            return Collections.emptyList();
        }

        @Override
        public MediaType getMediaType() {
            return null;
        }

        @Override
        public Locale getLanguage() {
            return null;
        }

        @Override
        public Map<String, Cookie> getCookies() {
            return Collections.emptyMap();
        }

        @Override
        public Date getDate() {
            return null;
        }

        @Override
        public int getLength() {
            return -1;
        }
    }
}
