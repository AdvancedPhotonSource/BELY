/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */

document.addEventListener('paste', pasteLogTextArea);

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
    }
}

function pasteLatestFileReference() {                
    let uploadRef = document.getElementById('logbookViewForm:lastFileReference'); 
    let fileRefMd = uploadRef.innerHTML; 
    
    if (fileRefMd === "") {
        console.error("File reference not set"); 
    }
    
    let textArea = document.getElementById('logbookViewForm:logbookLogEntryValue');    
    let newData = "\n\n" + fileRefMd + "\n\n";
    let exitingValue = $(textArea).val();
    let curPos = textArea.selectionStart; 
    
    newData=exitingValue.slice(0,curPos)+newData+exitingValue.slice(curPos); 
    $(textArea).val(newData);        
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
    console.log("Log Entry Double Clicked");
    var logEntryPanel = event.delegateTarget;
    var logObjectPanel = logEntryPanel.parentElement;
    var logEditButtons = logObjectPanel.getElementsByClassName('logEditButton');

    if (logEditButtons.length == 1) {
        var editButton = logEditButtons[0];
        editButton.click();
    }
});