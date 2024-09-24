/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */

document.addEventListener('paste', pasteLogTextArea);

const linkRegex = new RegExp("^(https:\/\/www\.|http:\/\/www\.|https:\/\/|http:\/\/)[a-zA-Z0-9]{2,}(\.[a-zA-Z0-9]{2,})(\.[a-zA-Z0-9]{2,})?");

function pasteLogTextArea(event) {
    // Ignore non text area 
    let srcElement = event.srcElement;
    if (srcElement.id !== 'logbookViewForm:logbookLogEntryValue') {
        return;
    }

    pastedFiles = event.clipboardData.files;

    if (pastedFiles.length > 0) {
        event.preventDefault();

        // Clear Upload Ref
        uploadRef = document.getElementById('logbookViewForm:lastFileReference');
        uploadRef.innerHTML = ""

        PF('loadingDialog').show();
        fileUploadWidget = PF('logEntryClipboardAttachmentFileUploadWidget');
        uploadInput = document.getElementById('logbookViewForm:logEntryClipboardAttachmentFileUpload');
        uploadInput.files = pastedFiles;
        fileUploadWidget.upload();
    } else {
        var pastedText = event.clipboardData.getData("Text");
        if (pastedText !== undefined && linkRegex.test(pastedText)) {
            // Link was pasted. 
            event.preventDefault();
            var newData = " [Link Text](" + pastedText + ") ";
            addCustomDataToLogEntryValue(newData);
        }
    }
}

function pasteLatestFileReference() {
    let uploadRef = document.getElementById('logbookViewForm:lastFileReference');
    let fileRefMd = uploadRef.innerHTML;

    if (fileRefMd === "") {
        console.error("File reference not set");
    }

    let newData = "\n\n" + fileRefMd + "\n\n";

    addCustomDataToLogEntryValue(newData);
}

function addCustomDataToLogEntryValue(newData) {
    let textArea = document.getElementById('logbookViewForm:logbookLogEntryValue');

    let exitingValue = $(textArea).val();
    let curPos = textArea.selectionStart;

    newData = exitingValue.slice(0, curPos) + newData + exitingValue.slice(curPos);
    $(textArea).val(newData);
}

function renderLogs() {
    logEntries = document.getElementsByClassName('logEntry'); 
    
    for (var entry of logEntries) {
        span = entry.children[0]; 
        if (span === undefined) {
            // Blank log document.
            continue; 
        }
        entry.innerHTML = span.innerText; 
    }
}

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

$('.logEntry').dblclick(function (event) {    
    var logEntryPanel = event.delegateTarget;
    var logObjectPanel = logEntryPanel.parentElement;
    
    children = logObjectPanel.children;         
    var footer = undefined; 
    
    for (var element of children) {
        if (element.className === 'logFooter') {
            footer = element; 
            break; 
        }
    }
    
    if (footer !== undefined) {
        var logEditButtons = footer.getElementsByClassName('logEditButton');       

        if (logEditButtons.length === 1) {
            var editButton = logEditButtons[0];
            editButton.click();
        } else {
            console.error("Too many matches for logEditButton found.");
        }
    } else {
         console.error("Could not find log footer.");
    }
});

function handleToggleRepliesButton(sender, widgetName) {    
    widget = PF(widgetName); 
    
    if (widget.cfg.collapsed) {
        sender.classList.remove('fa-chevron-down')
        sender.classList.add('fa-chevron-up');         
    } else {
        sender.classList.remove('fa-chevron-up')
        sender.classList.add('fa-chevron-down'); 
    }
    
    widget.toggle(); 
}
