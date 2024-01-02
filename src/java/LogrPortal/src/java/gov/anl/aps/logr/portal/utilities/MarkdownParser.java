/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.utilities;

import com.vladsch.flexmark.html.renderer.ResolvedLink;
import javax.validation.constraints.NotNull;
import com.vladsch.flexmark.ast.Image;
import com.vladsch.flexmark.html.renderer.*;
import com.vladsch.flexmark.html.HtmlRenderer;
import com.vladsch.flexmark.html.HtmlWriter;
import static com.vladsch.flexmark.html.renderer.CoreNodeRenderer.isSuppressedLinkPrefix;
import com.vladsch.flexmark.parser.Parser;
import com.vladsch.flexmark.util.ast.Node;
import com.vladsch.flexmark.util.ast.TextCollectingVisitor;
import com.vladsch.flexmark.util.data.DataHolder;
import com.vladsch.flexmark.util.data.MutableDataHolder;
import com.vladsch.flexmark.util.data.MutableDataSet;
import com.vladsch.flexmark.util.misc.Extension;
import com.vladsch.flexmark.util.sequence.BasedSequence;
import com.vladsch.flexmark.util.sequence.Escaping;
import gov.anl.aps.logr.common.constants.CdbPropertyValue;

import java.util.HashSet;
import java.util.Set;
import java.util.Arrays;

/**
 *
 * @author djarosz
 */
public class MarkdownParser {

    private static MutableDataHolder options = new MutableDataSet()
            .set(Parser.EXTENSIONS, Arrays.asList(
                    new Extension[]{
                        LogrFlexmarkExtension.create()
                    }
            ));

    private static Parser parser = Parser.builder(options).build();
    private static HtmlRenderer renderer = HtmlRenderer.builder(options).build();

    public static String parseMarkdownAsHTML(String text) {
        Node document = parser.parse(text);
        String html = renderer.render(document);

        return html;
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

        public LogrNodeRenderer(DataHolder options) {

        }

        @Override
        public Set<NodeRenderingHandler<?>> getNodeRenderingHandlers() {
            return new HashSet<>(Arrays.asList(
                    new NodeRenderingHandler<>(Image.class, this::render)
            ));
        }

        private void render(Image node, NodeRendererContext context, HtmlWriter html) {
            // Create a link to full size image. 
            ResolvedLink aLink = context.resolveLink(LinkType.LINK, node.getUrl().unescape(), null, null);
            html.attr("href", aLink.getUrl());
            html.attr("target", "_log_img");
            html.srcPos(node.getChars()).withAttr(aLink).tag("a");
            
            // Update image node to use scaled image             
            BasedSequence nodeUrl = node.getUrl();
            if (nodeUrl.startsWith("/")) {
                nodeUrl = nodeUrl.append(CdbPropertyValue.SCALED_IMAGE_EXTENSION);
                node.setUrl(nodeUrl);                 
            }                        

            // Standard image render function. Original is "private" 
            // See https://github.com/vsch/flexmark-java/blob/cc3a2f59ba6e532833f4805f8134b4dc966ff837/flexmark/src/main/java/com/vladsch/flexmark/html/renderer/CoreNodeRenderer.java#L617
            if (!(context.isDoNotRenderLinks() || isSuppressedLinkPrefix(node.getUrl(), context))) {
                String altText = new TextCollectingVisitor().collectAndGetText(node);                                                
                ResolvedLink resolvedLink = context.resolveLink(LinkType.IMAGE, node.getUrl().unescape(), null, null);
                String url = resolvedLink.getUrl();

                if (!node.getUrlContent().isEmpty()) {
                    // reverse URL encoding of =, &
                    String content = Escaping.percentEncodeUrl(node.getUrlContent()).replace("+", "%2B").replace("%3D", "=").replace("%26", "&amp;");
                    url += content;
                }

                html.attr("src", url);
                html.attr("alt", altText);

                // we have a title part, use that
                if (node.getTitle().isNotNull()) {
                    resolvedLink = resolvedLink.withTitle(node.getTitle().unescape());
                }

                html.attr(resolvedLink.getNonNullAttributes());
                html.srcPos(node.getChars()).withAttr(resolvedLink).tagVoid("img");
            }
            // End of image block 

            // Close a tag after adding image 
            html.tag("/a");
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
