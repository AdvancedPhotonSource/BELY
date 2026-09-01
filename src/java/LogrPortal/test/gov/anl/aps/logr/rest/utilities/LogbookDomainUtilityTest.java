/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.utilities;

import gov.anl.aps.logr.portal.constants.EntityTypeName;
import gov.anl.aps.logr.portal.constants.ItemDomainName;
import gov.anl.aps.logr.portal.model.db.beans.DomainFacade;
import gov.anl.aps.logr.portal.model.db.entities.Domain;
import gov.anl.aps.logr.portal.model.db.entities.EntityType;
import gov.anl.aps.logr.portal.model.db.entities.ItemType;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

// Plain-Java checks for LogbookDomainUtility; testSourceListIsNotMutated is the regression guard against filtering the domain's managed list in place.
public class LogbookDomainUtilityTest {

    // Reflection-based runner mirroring the existing MCP tests; no JUnit on the classpath.
    public static void main(String[] args) throws Exception {
        int passed = 0;
        int failed = 0;
        for (java.lang.reflect.Method m : LogbookDomainUtilityTest.class.getDeclaredMethods()) {
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

    private static final String TEMPLATE = EntityTypeName.template.getValue();

    // Builds a detached Domain; these entities construct fine without a container.
    private static Domain domainWithAllowedTypes(EntityType... types) {
        Domain domain = new Domain();
        domain.setAllowedEntityTypeList(new ArrayList<>(Arrays.asList(types)));
        return domain;
    }

    private static boolean containsName(List<EntityType> types, String name) {
        for (EntityType t : types) {
            if (name.equals(t.getName())) {
                return true;
            }
        }
        return false;
    }

    // Core behavior: the template type is excluded, everything else survives.
    static void testTemplateIsFilteredOut() {
        Domain domain = domainWithAllowedTypes(
                new EntityType(1, "Ops-Shift"),
                new EntityType(EntityTypeName.TEMPLATE_ID, TEMPLATE),
                new EntityType(2, "Maintenance"));

        List<EntityType> result = LogbookDomainUtility.getLogbookTypes(domain);

        check(!containsName(result, TEMPLATE), "template must be filtered out of the logbook types");
        check(result.size() == 2, "the two non-template types must survive, got " + result.size());
        check(containsName(result, "Ops-Shift") && containsName(result, "Maintenance"),
                "non-template types must be preserved");
    }

    // The actual regression guard for the in-place mutation bug.
    static void testSourceListIsNotMutated() {
        Domain domain = domainWithAllowedTypes(
                new EntityType(1, "Ops-Shift"),
                new EntityType(EntityTypeName.TEMPLATE_ID, TEMPLATE));
        List<EntityType> managedList = domain.getAllowedEntityTypeList();

        LogbookDomainUtility.getLogbookTypes(domain);

        check(managedList.size() == 2,
                "the domain's managed allowed-entity-type list must not be modified, size is " + managedList.size());
        check(containsName(managedList, TEMPLATE),
                "template must still be present on the domain after filtering a copy");
        check(domain.getAllowedEntityTypeList() == managedList,
                "the domain must still reference the same underlying list instance");
    }

    // The returned copy must be independent, so callers cannot corrupt the domain.
    static void testReturnedListIsNotTheManagedList() {
        Domain domain = domainWithAllowedTypes(new EntityType(1, "Ops-Shift"));

        List<EntityType> result = LogbookDomainUtility.getLogbookTypes(domain);

        check(result != domain.getAllowedEntityTypeList(),
                "callers must receive a copy, never the managed collection itself");
        result.clear();
        check(domain.getAllowedEntityTypeList().size() == 1,
                "mutating the returned list must not affect the domain");
    }

    // Under the old in-place logic, repeated calls degraded the shared list.
    static void testRepeatedCallsAreStable() {
        Domain domain = domainWithAllowedTypes(
                new EntityType(1, "Ops-Shift"),
                new EntityType(EntityTypeName.TEMPLATE_ID, TEMPLATE));

        List<EntityType> first = LogbookDomainUtility.getLogbookTypes(domain);
        List<EntityType> second = LogbookDomainUtility.getLogbookTypes(domain);
        List<EntityType> third = LogbookDomainUtility.getLogbookTypes(domain);

        check(first.size() == second.size() && second.size() == third.size(),
                "repeated calls on the same domain must return identically sized results");
        check(first.size() == 1, "each call must drop exactly the template entry");
    }

    // No template entry present is a normal case, not an error.
    static void testNoTemplatePresentIsANoOp() {
        Domain domain = domainWithAllowedTypes(new EntityType(1, "Ops-Shift"), new EntityType(2, "Maintenance"));

        List<EntityType> result = LogbookDomainUtility.getLogbookTypes(domain);

        check(result.size() == 2, "a domain without a template entry must be returned intact");
    }

    static void testEmptyAllowedListReturnsEmpty() {
        Domain domain = domainWithAllowedTypes();

        List<EntityType> result = LogbookDomainUtility.getLogbookTypes(domain);

        check(result != null && result.isEmpty(), "an empty allowed list must yield an empty result, not null");
    }

    static void testNullAllowedListReturnsEmpty() {
        Domain domain = new Domain();
        domain.setAllowedEntityTypeList(null);

        List<EntityType> result = LogbookDomainUtility.getLogbookTypes(domain);

        check(result != null && result.isEmpty(), "a null allowed list must yield an empty result, not throw");
    }

    static void testNullDomainReturnsEmptyTypes() {
        List<EntityType> result = LogbookDomainUtility.getLogbookTypes((Domain) null);

        check(result != null && result.isEmpty(), "a null domain must yield an empty result, not throw");
    }

    // Defensive: a null element must not blow up the filter.
    static void testNullEntryInAllowedListIsTolerated() {
        Domain domain = new Domain();
        domain.setAllowedEntityTypeList(new ArrayList<>(Arrays.asList(
                new EntityType(1, "Ops-Shift"), null, new EntityType(EntityTypeName.TEMPLATE_ID, TEMPLATE))));

        List<EntityType> result = LogbookDomainUtility.getLogbookTypes(domain);

        check(!containsNull(result) || result.size() == 2, "a null entry must not cause a NullPointerException");
        check(!containsName(stripNulls(result), TEMPLATE), "template must still be filtered alongside a null entry");
    }

    private static boolean containsNull(List<EntityType> types) {
        for (EntityType t : types) {
            if (t == null) {
                return true;
            }
        }
        return false;
    }

    private static List<EntityType> stripNulls(List<EntityType> types) {
        List<EntityType> result = new ArrayList<>();
        for (EntityType t : types) {
            if (t != null) {
                result.add(t);
            }
        }
        return result;
    }

    // Systems are passed through unfiltered, in their configured order.
    static void testGetLogbookSystemsReturnsItemTypeList() {
        Domain domain = new Domain();
        List<ItemType> itemTypes = new ArrayList<>(Arrays.asList(
                new ItemType(1, "Storage-Ring"), new ItemType(2, "Linac")));
        domain.setItemTypeList(itemTypes);

        List<ItemType> result = LogbookDomainUtility.getLogbookSystems(domain);

        check(result.size() == 2, "all configured systems must be returned");
        check(result.get(0).getName().equals("Storage-Ring"), "system ordering must be preserved");
    }

    static void testGetLogbookSystemsNullSafe() {
        check(LogbookDomainUtility.getLogbookSystems((Domain) null).isEmpty(),
                "a null domain must yield an empty system list, not throw");
        check(LogbookDomainUtility.getLogbookSystems(new Domain()).isEmpty(),
                "a domain with a null item type list must yield an empty list, not throw");
    }

    // Records which id the facade was asked for, so the lookup constant can be asserted.
    private static class RecordingDomainFacade extends DomainFacade {

        private final Domain domain;
        private Integer requestedId;

        RecordingDomainFacade(Domain domain) {
            this.domain = domain;
        }

        @Override
        public Domain find(Object id) {
            requestedId = (Integer) id;
            return domain;
        }
    }

    // The facade overload must look up the one logbook domain by its well-known id.
    static void testFacadeOverloadResolvesLogbookDomain() {
        Domain domain = domainWithAllowedTypes(
                new EntityType(1, "Ops-Shift"),
                new EntityType(EntityTypeName.TEMPLATE_ID, TEMPLATE));
        RecordingDomainFacade facade = new RecordingDomainFacade(domain);

        List<EntityType> result = LogbookDomainUtility.getLogbookTypes(facade);

        check(facade.requestedId != null && facade.requestedId == ItemDomainName.LOGBOOK_ID,
                "the facade must be queried with the logbook domain id, got " + facade.requestedId);
        check(result.size() == 1, "the facade overload must apply the same template filtering");
    }

    // The facade overload must not mutate the domain it resolves either.
    static void testFacadeOverloadDoesNotMutateDomain() {
        Domain domain = domainWithAllowedTypes(
                new EntityType(1, "Ops-Shift"),
                new EntityType(EntityTypeName.TEMPLATE_ID, TEMPLATE));
        List<EntityType> managedList = domain.getAllowedEntityTypeList();

        LogbookDomainUtility.getLogbookTypes(new RecordingDomainFacade(domain));

        check(managedList.size() == 2,
                "the facade overload must leave the managed list intact, size is " + managedList.size());
    }

    // Systems resolve through the facade the same way types do.
    static void testFacadeOverloadReturnsSystems() {
        Domain domain = new Domain();
        domain.setItemTypeList(new ArrayList<>(Arrays.asList(new ItemType(1, "Storage-Ring"))));

        List<ItemType> result = LogbookDomainUtility.getLogbookSystems(new RecordingDomainFacade(domain));

        check(result.size() == 1, "the facade overload must return the domain's systems");
    }

    // A null facade is treated like a null domain rather than throwing.
    static void testNullFacadeIsSafe() {
        check(LogbookDomainUtility.getLogbookDomain(null) == null,
                "a null facade must resolve to a null domain, not throw");
        check(LogbookDomainUtility.getLogbookTypes((DomainFacade) null).isEmpty(),
                "a null facade must yield empty logbook types, not throw");
        check(LogbookDomainUtility.getLogbookSystems((DomainFacade) null).isEmpty(),
                "a null facade must yield empty systems, not throw");
    }
}
