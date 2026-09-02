/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.constants;

public enum DownloadRouteMimeType {

    // Formats browsers can safely render in a tab.
    jpg(new String[]{"jpg", "jpeg"}, "image/jpeg", true),
    png(new String[]{"png"}, "image/png", true),
    gif(new String[]{"gif"}, "image/gif", true),
    pdf(new String[]{"pdf"}, "application/pdf", true),
    mp4(new String[]{"mp4", "mov"}, "video/mp4", true),
    mpeg(new String[]{"mpeg", "mpg"}, "video/mpeg", true),
    webm(new String[]{"webm"}, "video/webm", true),
    ogv(new String[]{"ogv"}, "video/ogg", true),

    // Rendering uploaded html inline would run its script in the app origin.
    html(new String[]{"htm", "html"}, "text/html", false),

    // Correct type so the OS picks the right app, but always delivered as a download.
    docx(new String[]{"docx"}, "application/vnd.openxmlformats-officedocument.wordprocessingml.document", false),
    xlsx(new String[]{"xlsx"}, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", false),
    pptx(new String[]{"pptx"}, "application/vnd.openxmlformats-officedocument.presentationml.presentation", false),
    doc(new String[]{"doc"}, "application/msword", false),
    xls(new String[]{"xls"}, "application/vnd.ms-excel", false),
    ppt(new String[]{"ppt"}, "application/vnd.ms-powerpoint", false),
    odt(new String[]{"odt"}, "application/vnd.oasis.opendocument.text", false),
    ods(new String[]{"ods"}, "application/vnd.oasis.opendocument.spreadsheet", false),
    odp(new String[]{"odp"}, "application/vnd.oasis.opendocument.presentation", false),
    zip(new String[]{"zip"}, "application/zip", false),
    csv(new String[]{"csv"}, "text/csv", false),
    txt(new String[]{"txt"}, "text/plain", false),
    json(new String[]{"json"}, "application/json", false),
    xml(new String[]{"xml"}, "application/xml", false),

    // Unrecognized extensions force a download rather than letting the browser guess.
    unknown(new String[]{""}, "application/octet-stream", false);

    private String[] extension;
    private String mimeType;
    private boolean inlineViewable;

    private DownloadRouteMimeType(String[] ext, String value, boolean inlineViewable) {
        this.extension = ext;
        this.mimeType = value;
        this.inlineViewable = inlineViewable;
    }

    private static DownloadRouteMimeType getForFilename(String fileName) {
        if (fileName == null) {
            return DownloadRouteMimeType.unknown;
        }

        String[] split = fileName.split("[.]");
        if (split.length < 2) {
            return DownloadRouteMimeType.unknown;
        }
        String ext = split[split.length - 1].toLowerCase();

        for (DownloadRouteMimeType value : DownloadRouteMimeType.values()) {
            for (String possibleExt : value.extension) {
                if (possibleExt.equals(ext)) {
                    return value;
                }
            }
        }

        return DownloadRouteMimeType.unknown;
    }

    public static String getTypeForFilename(String fileName) {
        return getForFilename(fileName).mimeType;
    }

    /** Whether the browser may display the file inline rather than downloading it. */
    public static boolean isInlineViewable(String fileName) {
        return getForFilename(fileName).inlineViewable;
    }
};
