window.onload = function () {
    window._showHideDetailLinkCallback = getCallbackShowHideDetailLink('url')
    window._showHideDetailLinkCallback(getPositionElement())
}

function beforeSubmit() {
    getPositionElement().disabled = false
}

function positionChanged(sender) {
    window._showHideDetailLinkCallback(sender)
}

function getPositionElement() {
    return document.getElementById('id_position')
}
