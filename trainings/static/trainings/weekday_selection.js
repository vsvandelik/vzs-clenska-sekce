function validateWeekdaySelection() {
    return validateAtLeastOneDayChecked(true)
}

function validateAtLeastOneDayChecked(report) {
    const checkboxes = getWeekdaysCheckboxes()
    const atLeastOneChecked = checkboxes.some(x => x.checked)
    if(atLeastOneChecked) {
        setReportValidity(checkboxes[0], '', report)
        return true
    }
    else {
        setReportValidity(checkboxes[0], 'Alespoň jeden den musí být vybrán', report)
        return false
    }
}

function weekdayCheckboxClicked(sender) {
    const checkboxes = getWeekdaysCheckboxes()
    if(sender.checked)
        setReportValidity(checkboxes[0], '', true)
}

function getWeekdaysCheckboxes() {
    return [... getWeekdaysSelectionElement()[0].getElementsByTagName('input')]
}

function getWeekdaysSelectionElement() {
    return $('#weekdays-selection')
}