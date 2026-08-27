/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp.schema;

import com.fasterxml.jackson.databind.node.ObjectNode;

/** Plain-Java checks for {@link JsonSchemaBuilder} — no JUnit is wired into this build, so {@link #main} is the runner. */
public class JsonSchemaBuilderTest {

    public static void main(String[] args) throws Exception {
        int passed = 0;
        int failed = 0;
        for (java.lang.reflect.Method m : JsonSchemaBuilderTest.class.getDeclaredMethods()) {
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

    static void testRequiredStringPropAppearsInRequiredAndProperties() {
        ObjectNode schema = new JsonSchemaBuilder()
                .requiredStringProp("searchText", "text to search")
                .build();
        check(schema.get("type").asText().equals("object"), "schema type must be object");
        check(schema.get("properties").get("searchText").get("type").asText().equals("string"), "searchText must be string");
        check(schema.get("properties").get("searchText").get("description").asText().equals("text to search"), "description must round-trip");
        check(schema.get("required").toString().contains("searchText"), "searchText must be in required");
    }

    static void testOptionalPropIsNotRequired() {
        ObjectNode schema = new JsonSchemaBuilder()
                .stringProp("filter", null)
                .build();
        check(!schema.has("required"), "schema with no required props must omit \"required\" entirely");
    }

    static void testIntegerArrayPropShape() {
        ObjectNode schema = new JsonSchemaBuilder()
                .integerArrayProp("logbookTypeIds", "type ids")
                .build();
        ObjectNode prop = (ObjectNode) schema.get("properties").get("logbookTypeIds");
        check(prop.get("type").asText().equals("array"), "must be array type");
        check(prop.get("items").get("type").asText().equals("integer"), "items must be integer type");
    }

    static void testEnumPropShape() {
        ObjectNode schema = new JsonSchemaBuilder()
                .enumProp("kind", "which kind", "logbookTypes", "systems", "templates")
                .build();
        ObjectNode prop = (ObjectNode) schema.get("properties").get("kind");
        check(prop.get("enum").size() == 3, "enum must have 3 values");
        check(prop.get("enum").get(0).asText().equals("logbookTypes"), "first enum value must round-trip in order");
        check(!schema.has("required") || !schema.get("required").toString().contains("kind"), "plain enumProp must not be required");
    }

    static void testRequiredEnumPropAddsToRequired() {
        ObjectNode schema = new JsonSchemaBuilder()
                .requiredEnumProp("kind", "which kind", "a", "b")
                .build();
        check(schema.get("required").toString().contains("kind"), "requiredEnumProp must add to required");
    }

    static void testMultiplePropsAccumulate() {
        ObjectNode schema = new JsonSchemaBuilder()
                .requiredIntegerProp("logDocumentId", null)
                .requiredIntegerProp("logId", null)
                .booleanProp("includeReplies", null)
                .build();
        check(schema.get("properties").size() == 3, "all three properties must be present");
        check(schema.get("required").size() == 2, "only the two required props must be listed");
    }
}
