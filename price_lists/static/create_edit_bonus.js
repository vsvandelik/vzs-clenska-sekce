window.onload = function () {
    window._basePath = getDjangoUrl('url').replace('/1/', '')
    qualificationChanged(getQualificationField())
}

function qualificationChanged(sender) {
    if (sender.value !== '') {
        getQualificationDetailLink().href = `${window._basePath}/${sender.value}`
        setDetailLinkVisibility(true)
    }
    else {
        setDetailLinkVisibility(false)
    }
}
function getQualificationField() {
    return document.getElementById('id_feature')
}

function getQualificationDetailLink() {
    return document.getElementById('detail-link')
}

function setDetailLinkVisibility(state) {
    getQualificationDetailLink().style.display = state ? '' : 'none'
}
