/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */

/**
 * Adds copy buttons to all <pre><code> blocks within a container.
 * @param {Element} [container=document] - The container to search within.
 */
function addCodeBlockCopyButtons(container) {
    try {
        container = container || document;
        var preElements = container.querySelectorAll('pre');

        for (var i = 0; i < preElements.length; i++) {
            var pre = preElements[i];
            var code = pre.querySelector('code');
            if (!code) continue;
            if (pre.querySelector('.code-copy-btn')) continue;

            var btn = document.createElement('button');
            btn.className = 'code-copy-btn';
            btn.type = 'button';
            btn.innerHTML = '<i class="fa fa-copy"></i>';
            btn.setAttribute('onclick', 'copyCodeBlock(this); return false;');
            pre.appendChild(btn);
        }
    } catch (e) {
        console.error('Failed to add code block copy buttons:', e);
    }
}

function copyCodeBlock(btn) {
    var code = btn.parentElement.querySelector('code');
    if (!code) return;

    navigator.clipboard.writeText(code.textContent).then(function () {
        btn.innerHTML = '<i class="fa fa-check"></i>';
        setTimeout(function () {
            btn.innerHTML = '<i class="fa fa-copy"></i>';
        }, 1500);
    }).catch(function (e) {
        console.error('Failed to copy code block:', e);
    });
}
