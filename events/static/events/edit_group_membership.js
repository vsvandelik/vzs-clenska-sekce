window.onload = function () {
    window._showHideDetailLinkCallback = getCallbackShowHideDetailLink('url')
    window._showHideDetailLinkCallback(getGroupField())
}

function groupChanged(sender) {
    window._showHideDetailLinkCallback(sender)
}

function getGroupField() {
    return document.getElementById('id_group')
}
