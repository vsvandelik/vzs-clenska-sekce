window.addEventListener('load', event => {
    window._showHideDetailLinkCallback = getCallbackShowHideDetailLink('url')
    window._showHideDetailLinkCallback(getPersonElement())
    $('form').on('submit', beforeSubmit)
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

function beforeSubmit() {
    getPersonElement().disabled = false
}