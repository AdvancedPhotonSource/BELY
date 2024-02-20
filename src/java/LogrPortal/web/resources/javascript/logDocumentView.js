/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */

function ScrollToLog(logId) {
    if (logId) {
        var location = 'log-' + logId;
        window.location.hash = location;

        element = document.getElementById(location);
        if (element) {
            element.classList.add("activeLogEntry");
        }
    }
}

function toggleTimestamps() {
    var timestampPanels = document.getElementsByClassName('logTimestamp');

    for (var i = 0; i < timestampPanels.length; i++) {
        var widgetVar = timestampPanels[i].getAttribute('data-widget');
        PF(widgetVar).toggle();
    }
}
