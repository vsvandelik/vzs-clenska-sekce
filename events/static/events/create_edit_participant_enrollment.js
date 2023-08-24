window.addEventListener('load', event => {
    window._showHideDetailLinkCallback = getCallbackShowHideDetailLink('url')
    window._showHideDetailLinkCallback(getPersonElement())
    $('form').on('submit', enablePersonElement)
})
function personChanged(sender) {
    window._showHideDetailLinkCallback(sender)
}

function getPersonElement() {
    return document.getElementById('id_person')
}

function getStateElement() {
    return document.getElementById('id_state')
}

function enablePersonElement() {
    getPersonElement().disabled = false
}