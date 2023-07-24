window.onload = function() {
    window._basePath = getDjangoUrl('url').replace('/1/', '')
    const positionElement = getPositionElement()
    positionChanged(positionElement, positionElement.value)
}

function beforeSubmit() {
    getPositionElement().disabled = false
}

function positionChanged(sender) {
    if(sender.value === undefined || sender.value === '') {
        setDetailLinkVisibility(false)
    }
    else {
        const new_position_id = sender.value
        setDetailLinkVisibility(true)
        getDetailLinkElement().href = `${window._basePath}/${new_position_id}/`
    }
}

function getPositionElement() {
    return document.getElementById('id_position')
}

function getDetailLinkElement() {
    return document.getElementById('detail-link')
}

function setDetailLinkVisibility(state) {
    getDetailLinkElement().style.display = state ? '' : 'none'
}