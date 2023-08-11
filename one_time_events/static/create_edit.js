function dateChanged() {
    validateDate()
}

function beforeSubmit() {
    return validateForm()
}

function validateForm() {
    return validateDate(true)
}

function validateDate(report = false) {
    const timeStartDate = convertCzechDate(document.getElementById('id_time_start').value)
    const timeEndEl = document.getElementById('id_time_end')
    const timeEndDate = convertCzechDate(timeEndEl.value)
    const span = timeEndDate.getTime() - timeStartDate.getTime()
    if (span <= 0 || isNaN(span)) {
        setReportValidity(timeEndEl, 'Konec události nesmí být dříve než její začátek', report)
        return false
    } else {
        setReportValidity(timeEndEl, '', report)
        return true
    }
}

window.onload = function() {
    window._basePath = getDjangoUrl('url').replace('/1/', '')
    priceListChanged(getPriceListField())
}