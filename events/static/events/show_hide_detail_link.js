function getCallbackShowHideDetailLink() {
    const urlSplit = window.location.href.split('/')
    const baseUrl = `${urlSplit[0]}//${urlSplit[2]}`
    const basePath = document.getElementById('url').getAttribute('data-url')
    window._basePath = `${baseUrl}${basePath}`.replace('/1/', '')
    return callback
}

function getDetailLinkElement() {
    return document.getElementById('detail-link')
}

function setDetailLinkVisibility(state) {
    getDetailLinkElement().style.display = state ? '' : 'none'
}

function callback(sender) {
    if (sender.value === undefined || sender.value === '') {
        setDetailLinkVisibility(false)
    } else {
        setDetailLinkVisibility(true)
        getDetailLinkElement().href = `${window._basePath}/${sender.value}/`
    }
}