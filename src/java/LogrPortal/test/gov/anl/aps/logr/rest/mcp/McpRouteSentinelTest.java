/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp;

import java.nio.charset.StandardCharsets;
import java.util.Base64;

/** Plain-Java checks for {@link McpRoute#decodeSentinel}, the {@code =?base64?<b64>?=} unwrapper used for Mcp-Name. */
public class McpRouteSentinelTest {

    public static void main(String[] args) throws Exception {
        int passed = 0;
        int failed = 0;
        for (java.lang.reflect.Method m : McpRouteSentinelTest.class.getDeclaredMethods()) {
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

    static void testPlainValueWithoutSentinelIsUnchanged() {
        check(McpRoute.decodeSentinel("bely_search").equals("bely_search"), "a plain tool name must pass through unchanged");
    }

    static void testNullIsNull() {
        check(McpRoute.decodeSentinel(null) == null, "decodeSentinel(null) must return null, not throw");
    }

    static void testValidSentinelDecodesUtf8Payload() {
        String encoded = Base64.getEncoder().encodeToString("bely_search".getBytes(StandardCharsets.UTF_8));
        String wrapped = "=?base64?" + encoded + "?=";
        check(McpRoute.decodeSentinel(wrapped).equals("bely_search"), "a valid sentinel must decode to its original payload");
    }

    static void testValidSentinelDecodesNonAsciiPayload() {
        String original = "bely_日本語";
        String encoded = Base64.getEncoder().encodeToString(original.getBytes(StandardCharsets.UTF_8));
        String wrapped = "=?base64?" + encoded + "?=";
        check(McpRoute.decodeSentinel(wrapped).equals(original), "non-ASCII payloads are exactly what the sentinel exists for");
    }

    // Sentinel-shaped but not valid base64 (underscores) — must fall back to the literal value, not throw.
    static void testSentinelShapedButInvalidBase64FallsBackToLiteral() {
        String wrapped = "=?base64?bely_search?=";
        check(McpRoute.decodeSentinel(wrapped).equals(wrapped),
                "an invalid base64 payload must fall back to the original literal value, not throw");
    }

    static void testEmptyPayloadDecodesToEmptyString() {
        check(McpRoute.decodeSentinel("=?base64??=").equals(""), "an empty base64 payload is validly empty, not a fallback case");
    }
}
