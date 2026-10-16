package gov.anl.aps.logr.portal.utilities;

import gov.anl.aps.logr.portal.model.db.entities.EntityInfo;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook;
import gov.anl.aps.logr.portal.model.db.entities.Log;
import gov.anl.aps.logr.portal.model.db.entities.LogTopic;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
import java.util.Arrays;
import java.util.Collections;
import java.util.Date;

/** Plain-Java regression checks; this project does not wire JUnit into the test classpath. */
public class LogbookPdfExportUtilityTest {

    public static void main(String[] args) throws Exception {
        Log first = log(1, "First <entry>\n\n| A | B |\n|---|---|\n| 1 | 2 |", "alice");
        Log reply = log(2, "Reply", "bob");
        first.setChildLogList(Collections.singletonList(reply));
        Log second = log(3, "Second", "carol");

        TestDocument document = new TestDocument();
        document.setId(7);
        document.setName("Shift <A/B>");
        document.setTestLogList(Arrays.asList(first, second));

        String html = LogbookPdfExportUtility.buildDocumentHtml(document);
        assertContains(html, "Shift &lt;A/B&gt;");
        assertContains(html, "First <entry>");
        assertContains(html, "<table>");
        assertContains(html, "Author:</strong> alice");
        assertContains(html, "Topic:</strong> Operations");
        assertTrue(html.indexOf("First <entry>") < html.indexOf("Reply"), "reply follows parent");
        assertTrue(html.indexOf("Reply") < html.indexOf("Second"), "entries retain chronological order");
        assertContains(html, "class=\"log-entry reply\"");
        assertTrue(!html.contains("unreferenced.dat"), "unreferenced attachments are absent");
        assertTrue(LogbookPdfExportUtility.getDocumentFilename(document).equals("Shift-A-B-7.pdf"), "safe document filename");
        assertTrue(LogbookPdfExportUtility.getEntryFilename(first).equals("log-entry-1.pdf"), "stable entry filename");

        String entryHtml = LogbookPdfExportUtility.buildEntryHtml(document, first);
        assertContains(entryHtml, "Document ID:</strong> 7");
        byte[] pdf = LogbookPdfExportUtility.renderPdf(entryHtml);
        assertTrue(pdf.length > 4, "PDF has content");
        assertTrue(new String(pdf, 0, 4, "US-ASCII").equals("%PDF"), "valid PDF signature");
    }

    private static Log log(int id, String text, String username) {
        UserInfo user = new UserInfo();
        user.setUsername(username);
        LogTopic topic = new LogTopic();
        topic.setName("Operations");
        Date entered = new Date(id * 1000L);
        Log log = new Log(id, text, entered);
        log.setEnteredByUser(user);
        log.setLastModifiedByUser(user);
        log.setLastModifiedOnDateTime(entered);
        log.setLogTopic(topic);
        log.setChildLogList(Collections.emptyList());
        return log;
    }

    private static void assertContains(String value, String expected) {
        assertTrue(value.contains(expected), "expected: " + expected);
    }

    private static void assertTrue(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }

    private static class TestDocument extends ItemDomainLogbook {
        private java.util.List<Log> testLogList;

        void setTestLogList(java.util.List<Log> testLogList) {
            this.testLogList = testLogList;
        }

        @Override
        public java.util.List<Log> getLogList() {
            return testLogList;
        }

        @Override
        public EntityInfo getEntityInfo() {
            return null;
        }

        @Override
        public String getEntityTypeString() {
            return "Ops Shift";
        }

        @Override
        public java.util.List<ItemDomainLogbook> getLogbookSections() {
            return Collections.singletonList(this);
        }
    }
}
