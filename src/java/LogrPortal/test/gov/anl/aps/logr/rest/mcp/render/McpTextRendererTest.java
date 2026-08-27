/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp.render;

import java.util.Date;

/** Plain-Java checks for {@link McpTextRenderer}'s truncation boundaries; see {@code JsonSchemaBuilderTest} for why no JUnit. */
public class McpTextRendererTest {

    public static void main(String[] args) throws Exception {
        int passed = 0;
        int failed = 0;
        for (java.lang.reflect.Method m : McpTextRendererTest.class.getDeclaredMethods()) {
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

    static void testTruncateAtExactBoundaryIsUnchanged() {
        String text = "0123456789";
        check(McpTextRenderer.truncate(text, 10).equals(text), "text.length() == maxChars must not be truncated");
    }

    static void testTruncateOneOverBoundaryIsCut() {
        String text = "0123456789X";
        check(McpTextRenderer.truncate(text, 10).equals("0123456789"), "text.length() == maxChars + 1 must cut to exactly maxChars");
    }

    static void testTruncateNullIsEmpty() {
        check(McpTextRenderer.truncate(null, 10).equals(""), "truncate(null, _) must be empty string, not null");
    }

    static void testTruncateWithMarkerUnderLimitIsUnchanged() {
        String text = "short";
        check(McpTextRenderer.truncateWithMarker(text, 100, "call X").equals(text), "under the limit, no marker should be appended");
    }

    static void testTruncateWithMarkerAtExactBoundaryIsUnchanged() {
        String text = "0123456789";
        check(McpTextRenderer.truncateWithMarker(text, 10, "call X").equals(text), "text.length() == maxChars must not get a marker");
    }

    static void testTruncateWithMarkerOverLimitNamesFollowUp() {
        String text = "0123456789XYZ";
        String result = McpTextRenderer.truncateWithMarker(text, 10, "call bely_get_log_entry logId=5");
        check(result.startsWith("0123456789"), "truncated body must be preserved");
        check(result.contains("truncated 3 of 13 chars"), "marker must report exact truncated/total counts, got: " + result);
        check(result.contains("call bely_get_log_entry logId=5"), "marker must name the exact follow-up call");
    }

    static void testCollapseWhitespaceTrimsAndCollapses() {
        String text = "  hello \n\n  world\t!  ";
        check(McpTextRenderer.collapseWhitespace(text).equals("hello world !"), "must trim and collapse runs of whitespace to one space");
    }

    static void testCollapseWhitespaceNullIsEmpty() {
        check(McpTextRenderer.collapseWhitespace(null).equals(""), "collapseWhitespace(null) must be empty string");
    }

    static void testIsoDateNullIsQuestionMark() {
        check(McpTextRenderer.isoDate(null).equals("?"), "isoDate(null) must be \"?\", not throw or return null");
    }

    static void testIsoDateFormatsAsUtc() {
        Date epoch = new Date(0L);
        check(McpTextRenderer.isoDate(epoch).equals("1970-01-01T00:00:00Z"), "epoch must format as 1970-01-01T00:00:00Z");
    }

    static void testSafeReturnsValueOnSuccess() {
        check(McpTextRenderer.safe(() -> "ok").equals("ok"), "safe() must pass through a successful supplier's value");
    }

    static void testSafeReturnsQuestionMarkOnNull() {
        check(McpTextRenderer.safe(() -> null).equals("?"), "safe() must map a null supplier result to \"?\"");
    }

    static void testSafeCatchesRuntimeException() {
        String result = McpTextRenderer.safe(() -> {
            throw new NullPointerException("simulated unfetchable lazy relation");
        });
        check(result.equals("?"), "safe() must catch RuntimeException from the supplier and degrade to \"?\"");
    }

    static void testNz() {
        check(McpTextRenderer.nz(null).equals(""), "nz(null) must be empty string");
        check(McpTextRenderer.nz("x").equals("x"), "nz(x) must pass through unchanged");
    }

    static void testCapResultUnderLimitIsUnchanged() {
        String text = "short result";
        check(McpTextRenderer.capResult(text).equals(text), "under MAX_RESULT_CHARS, capResult must not alter the text");
    }

    static void testCapResultOverLimitTruncatesToExactCap() {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < McpRenderLimits.MAX_RESULT_CHARS + 500; i++) {
            sb.append('a');
        }
        String result = McpTextRenderer.capResult(sb.toString());
        String[] parts = result.split("\n… \\[result truncated", 2);
        check(parts[0].length() == McpRenderLimits.MAX_RESULT_CHARS,
                "capResult must cut the body to exactly MAX_RESULT_CHARS, got " + parts[0].length());
        check(result.contains("truncated at " + McpRenderLimits.MAX_RESULT_CHARS), "cap marker must name the exact limit");
    }
}
