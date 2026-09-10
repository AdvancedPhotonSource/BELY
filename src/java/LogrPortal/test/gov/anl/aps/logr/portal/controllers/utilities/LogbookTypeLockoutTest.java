/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.utilities;

import gov.anl.aps.logr.common.exceptions.InvalidObjectState;
import gov.anl.aps.logr.portal.model.db.entities.Domain;
import gov.anl.aps.logr.portal.model.db.entities.EntityInfo;
import gov.anl.aps.logr.portal.model.db.entities.EntityType;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook;
import java.util.ArrayList;
import java.util.Arrays;

public class LogbookTypeLockoutTest {

    public static void main(String[] args) throws Exception {
        int passed = 0;
        int failed = 0;
        for (java.lang.reflect.Method method : LogbookTypeLockoutTest.class.getDeclaredMethods()) {
            if (method.getName().startsWith("test") && method.getParameterCount() == 0) {
                try {
                    method.setAccessible(true);
                    method.invoke(null);
                    System.out.println("PASS " + method.getName());
                    passed++;
                } catch (java.lang.reflect.InvocationTargetException ex) {
                    System.out.println("FAIL " + method.getName() + ": " + ex.getCause());
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

    static void testGroupingTypeIsRejected() throws Exception {
        EntityType parent = new EntityType(1, "Operations");
        parent.setDisplayName("Operations");
        EntityType child = new EntityType(2, "Storage-Ring");
        parent.setEntityTypeChildren(new ArrayList<>(Arrays.asList(child)));

        try {
            new ItemDomainLogbookControllerUtility().completeCreateEntityInstance(
                    new ItemDomainLogbook(), parent, null, false);
            throw new AssertionError("a grouping type must be rejected");
        } catch (InvalidObjectState ex) {
            check(ex.getMessage().contains("grouping logbook type"),
                    "the rejection must explain that the type is a grouping type");
        }
    }

    static void testNullTypeIsRejected() throws Exception {
        try {
            new ItemDomainLogbookControllerUtility().completeCreateEntityInstance(
                    new ItemDomainLogbook(), null, null, false);
            throw new AssertionError("a null logbook type must be rejected");
        } catch (InvalidObjectState ex) {
            check(ex.getMessage().contains("required"),
                    "the rejection must explain that a logbook type is required");
        }
    }

    static void testLeafTypeIsAccepted() throws Exception {
        EntityType leaf = new EntityType(1, "Storage-Ring");
        leaf.setEntityTypeChildren(new ArrayList<>());
        Domain domain = new Domain();
        domain.setAllowedEntityTypeList(new ArrayList<>(Arrays.asList(leaf)));
        ItemDomainLogbook document = new ItemDomainLogbook();
        document.init(domain, new EntityInfo());

        ItemDomainLogbook result = new ItemDomainLogbookControllerUtility()
                .completeCreateEntityInstance(document, leaf, null, false);

        check(result == document, "the utility must return the supplied document");
        check(result.getEntityTypeList().size() == 1
                && result.getEntityTypeList().get(0).equals(leaf),
                "the leaf type must be assigned to the document");
    }
}
