/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.utilities;

import com.vladsch.flexmark.html.renderer.ResolvedLink;
import javax.validation.constraints.NotNull;
import com.vladsch.flexmark.ast.Image;
import com.vladsch.flexmark.ast.Link;
import com.vladsch.flexmark.html.renderer.*;
import com.vladsch.flexmark.html.HtmlRenderer;
import com.vladsch.flexmark.html.HtmlWriter;
import static com.vladsch.flexmark.html.renderer.CoreNodeRenderer.isSuppressedLinkPrefix;
import com.vladsch.flexmark.parser.Parser;
import com.vladsch.flexmark.util.ast.Node;
import com.vladsch.flexmark.util.ast.TextCollectingVisitor;
import com.vladsch.flexmark.util.data.DataHolder;
import com.vladsch.flexmark.util.data.DataKey;
import com.vladsch.flexmark.util.data.MutableDataHolder;
import com.vladsch.flexmark.util.data.MutableDataSet;
import com.vladsch.flexmark.util.misc.Extension;
import com.vladsch.flexmark.util.sequence.BasedSequence;
import com.vladsch.flexmark.util.sequence.Escaping;
import com.vladsch.flexmark.ext.tables.TablesExtension;
import gov.anl.aps.logr.common.constants.CdbProperty;
import gov.anl.aps.logr.common.constants.CdbPropertyValue;

import java.io.File;
import java.util.HashSet;
import java.util.Set;
import java.util.Arrays;

/**
 *
 * @author djarosz
 */
public class MarkdownParser {

    private final static String markdownExample = "### Bullet List\n"
            + "\n\n"
            + "- Bullet list item\n"
            + "  - Sub item\n"
            + "- Another item\n"
            + "\n"
            + "### Numbered List\n"
            + "\n\n"
            + "1. Numbered List.\n"
            + "1. Another numbered item.\n"
            + "1. Third item. \n"
            + "\n"
            + "\n"
            + "### Text Decorate\n"
            + "\n"
            + "- **bold** text\n"
            + "- _italicized_ text\n"
            + "\n\n"
            + "## Link\n"
            + "\nMarkdown\n"
            + "[help](https://www.markdownguide.org/basic-syntax/)\n"
            + "\n\n"
            + "### Code Block\n\n"
            + "```\n"
            + "monospaced code content goes here\n"
            + "```\n"
            + "\n\n"
            + "### Table\n\n"
            + "| Column1 | Column2 | Column3 |\n"
            + "| --- | --- | --- |\n"
            + "| Cell 1 | Cell 2 | Cell 3 |\n"
            + "\n\n"
            + "### Heading Levels\n"
            + "# Level 1 Heading\n"
            + "## Level 2 Heading\n"
            + "### Level 3 Heading\n";
            

    private static String contextRoot = null;
    private static String permanentContextRootUrl = null;
    
    private static final String LOG_ATTACHMENT_PREFIX = "/log/attachments/"; 
    private static final String API_DOWNLOAD_PREFIX = "/api/Downloads/Attachments/"; 

    private static String markdownExampleAsHtml = null;

    private static final DataKey<Boolean> PDF_EXPORT = new DataKey<>("PDF_EXPORT", false);

    private static MutableDataHolder options = new MutableDataSet()
            .set(Parser.EXTENSIONS, Arrays.asList(
                    new Extension[]{
                        LogrFlexmarkExtension.create(),
                        TablesExtension.create()
                    }
            ));

    private static Parser parser = Parser.builder(options).build();
    private static HtmlRenderer renderer = HtmlRenderer.builder(options).build();

    public static String parseMarkdownAsHTML(String text) {
        return renderMarkdown(text, renderer);
    }

    public static String parseMarkdownAsPdfHTML(String text) {
        MutableDataHolder pdfOptions = new MutableDataSet(options).set(PDF_EXPORT, true);
        return renderMarkdown(text, HtmlRenderer.builder(pdfOptions).build());
    }

    private static String renderMarkdown(String text, HtmlRenderer htmlRenderer) {
        Node document = parser.parse(text == null ? "" : text);
        return htmlRenderer.render(document);
    }

    public static String getMarkdownExampleText() {
        return markdownExample;
    }

    public static String getMarkdownExampleHtml() {
        if (markdownExampleAsHtml == null) {
            markdownExampleAsHtml = parseMarkdownAsHTML(markdownExample);
        }

        return markdownExampleAsHtml;
    }

    static class LogrFlexmarkExtension implements HtmlRenderer.HtmlRendererExtension {

        @Override
        public void rendererOptions(@NotNull MutableDataHolder options) {
            // add any configuration settings to options you want to apply to everything, here
        }

        @Override
        public void extend(@NotNull HtmlRenderer.Builder htmlRendererBuilder, @NotNull String rendererType) {
            htmlRendererBuilder.nodeRendererFactory(new LogrNodeRenderer.Factory());
        }

        static LogrFlexmarkExtension create() {
            return new LogrFlexmarkExtension();
        }
    }

    // Node renderer to customize markdown html output. 
    static class LogrNodeRenderer implements NodeRenderer {

        private final boolean pdfExport;

        public LogrNodeRenderer(DataHolder options) {
            pdfExport = PDF_EXPORT.get(options);
        }

        @Override
        public Set<NodeRenderingHandler<?>> getNodeRenderingHandlers() {
            return new HashSet<>(Arrays.asList(
                    new NodeRenderingHandler<>(Image.class, this::render),
                    new NodeRenderingHandler<>(Link.class, this::render)
            ));
        }

        private String getContextRoot() {
            if (contextRoot == null) {
                contextRoot = SessionUtility.getContextRoot();
            }
            return contextRoot;
        }

        private String getPermanentContextRootUrl() {
            if (permanentContextRootUrl == null) {
                permanentContextRootUrl = ConfigurationUtility.getPortalProperty(
                        CdbProperty.PERMANENT_CONTEXT_ROOT_URL_PROPERTY_NAME);
            }
            return permanentContextRootUrl;
        }
        
        private String getAttachmentEndpoint(String url, boolean scaled) {
            if (url.startsWith(LOG_ATTACHMENT_PREFIX)) {
                String attachmentName = url.substring(LOG_ATTACHMENT_PREFIX.length());
                if (pdfExport && scaled) {
                    return getPdfAttachmentUrl(attachmentName, true);
                }

                String root = pdfExport ? getPermanentContextRootUrl() : getContextRoot();
                url = root + API_DOWNLOAD_PREFIX + attachmentName;
                if (scaled) {
                    url = url + '/' + CdbPropertyValue.SCALED_IMAGE_SCALING;
                }
            }

            return url;
        }

        private String getPdfAttachmentUrl(String attachmentName, boolean scaled) {
            File attachmentFile = new File(StorageUtility.getFileSystemLogAttachmentPath(attachmentName));
            if (scaled) {
                File scaledFile = new File(attachmentFile.getPath() + CdbPropertyValue.SCALED_IMAGE_EXTENSION);
                if (scaledFile.isFile()) {
                    attachmentFile = scaledFile;
                }
            }
            return attachmentFile.toURI().toString();
        }

        private void render(Image node, NodeRendererContext context, HtmlWriter html) {
            BasedSequence nodeUrl = node.getUrl();
            ResolvedLink aLink = context.resolveLink(LinkType.LINK, node.getUrl().unescape(), null, null);
            ResolvedLink imgLink = context.resolveLink(LinkType.IMAGE, node.getUrl().unescape(), null, null);
            
            String fullResUrl = aLink.getUrl();
            String scaledUrl = imgLink.getUrl();

            boolean storedAttachment = nodeUrl.startsWith("/");
            if (storedAttachment) {
                String attachmentName = nodeUrl.subSequence(LOG_ATTACHMENT_PREFIX.length(), nodeUrl.length()).toString();
                if (pdfExport) {
                    scaledUrl = getPdfAttachmentUrl(attachmentName, false);
                } else {
                    fullResUrl = getAttachmentEndpoint(fullResUrl, false);
                    scaledUrl = getAttachmentEndpoint(scaledUrl, true);
                }
            }

            if (!pdfExport) {
                // Web images link to the full-size attachment.
                html.attr("href", fullResUrl);
                html.attr("target", "_log_img");
                html.srcPos(node.getChars()).withAttr(aLink).tag("a");
            }

            // Standard image render function. Original is "private" 
            // See https://github.com/vsch/flexmark-java/blob/cc3a2f59ba6e532833f4805f8134b4dc966ff837/flexmark/src/main/java/com/vladsch/flexmark/html/renderer/CoreNodeRenderer.java#L617
            if (!(context.isDoNotRenderLinks() || isSuppressedLinkPrefix(node.getUrl(), context))) {
                String altText = new TextCollectingVisitor().collectAndGetText(node);

                if (!node.getUrlContent().isEmpty()) {
                    // reverse URL encoding of =, &
                    String content = Escaping.percentEncodeUrl(node.getUrlContent()).replace("+", "%2B").replace("%3D", "=").replace("%26", "&amp;");
                    scaledUrl += content;
                }

                html.attr("src", scaledUrl);
                html.attr("alt", altText);

                // we have a title part, use that
                if (node.getTitle().isNotNull()) {
                    imgLink = imgLink.withTitle(node.getTitle().unescape());
                }

                html.attr(imgLink.getNonNullAttributes());
                html.srcPos(node.getChars()).withAttr(imgLink).tagVoid("img");
            }
            // End of image block 

            if (!pdfExport) {
                html.tag("/a");
            }
        }                

        //See https://github.com/vsch/flexmark-java/blob/cc3a2f59ba6e532833f4805f8134b4dc966ff837/flexmark/src/main/java/com/vladsch/flexmark/html/renderer/CoreNodeRenderer.java#L642
        void render(Link node, NodeRendererContext context, HtmlWriter html) {
            if (context.isDoNotRenderLinks() || isSuppressedLinkPrefix(node.getUrl(), context)) {
                context.renderChildren(node);
            } else {
                ResolvedLink resolvedLink = context.resolveLink(LinkType.LINK, node.getUrl().unescape(), null, null);
                String url = resolvedLink.getUrl();

                url = getAttachmentEndpoint(url, false);

                html.attr("href", url);
                html.attr("target", "_log_link");

                // we have a title part, use that
                if (node.getTitle().isNotNull()) {
                    resolvedLink = resolvedLink.withTitle(node.getTitle().unescape());
                }

                html.attr(resolvedLink.getNonNullAttributes());
                html.srcPos(node.getChars()).withAttr(resolvedLink).tag("a");
                context.renderChildren(node);
                html.tag("/a");
            }
        }

        public static class Factory implements NodeRendererFactory {

            @NotNull
            @Override
            public NodeRenderer apply(@NotNull DataHolder options) {
                return new LogrNodeRenderer(options);
            }
        }
    }

}
