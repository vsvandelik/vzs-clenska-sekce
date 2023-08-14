window.onload = function () {
    window._basePath = getDjangoUrl('url').replace('/1/', '')
    groupChanged(getGroupField())
}

function groupChanged(sender) {
    if(sender.value === undefined || sender.value === '' || sender.disabled) {
        setDetailLinkVisibility(false)
    }
    else {
        setDetailLinkVisibility(true)
        getGroupDetailLink().href = `${window._basePath}/${sender.value}/`
    }
}

function getGroupField() {
    return document.getElementById('id_group')
}

function getGroupDetailLink() {
    return document.getElementById('detail-link')
}

function setDetailLinkVisibility(state) {
    getGroupDetailLink().style.display = state ? '' : 'none'
}
