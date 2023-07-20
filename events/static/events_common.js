function priceListChanged(sender) {
    if (sender.value !== '') {
        getPriceListDetailLink().href = `${window._basePath}/${sender.value}`
        setDetailLinkVisibility(true)
    }
    else {
        setDetailLinkVisibility(false)
    }
}
function getPriceListField() {
    return document.getElementById('id_price_list')
}

function getPriceListDetailLink() {
    return document.getElementById('detail-link')
}

function setDetailLinkVisibility(state) {
    getPriceListDetailLink().style.display = state ? '' : 'none'
}
