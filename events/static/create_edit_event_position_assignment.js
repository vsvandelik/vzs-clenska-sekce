window.onload = function() {
    const urlSplit = window.location.href.split('/')
    window._baseUrl = `${urlSplit[0]}//${urlSplit[2]}`
    window._basePath = document.getElementById('url').getAttribute('data-url').replace('/1/', '')
    const positionElement = getPositionElement()
    positionChanged(positionElement, positionElement.value)
}

function positionChanged(sender) {
    if(sender.value === undefined || sender.value === '') {
        setDetailLinkVisibility(false)
    }
    else {
        const new_position_id = sender.value
        setDetailLinkVisibility(true)
        getDetailLinkElement().href = `${window._baseUrl}${window._basePath}/${new_position_id}/`
    }
}

function getPositionElement() {
    return document.getElementById('id_position')
}

function getDetailLinkElement() {
    return document.getElementById('detailLink')
}

function setDetailLinkVisibility(state) {
    getDetailLinkElement().style.display = state ? '' : 'none'
}