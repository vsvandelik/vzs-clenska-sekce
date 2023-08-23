window.addEventListener('load', event => {
    $('form').on('submit', beforeSubmit)
    stateChanged()
})

function stateChanged() {
    const newValue = getStateElement().value
    const weekdaysSelectionElement = getWeekdaysSelectionElement()
    if(newValue !== 'odmitnut') {
        weekdaysSelectionElement.show()
        setWeekdaysState(true)
    }
    else {
        weekdaysSelectionElement.hide()
        setWeekdaysState(false)
    }
}

function getWeekdaysSelectionElement() {
    return $('#weekdays-selection')
}

function setWeekdaysState(state) {
    const inputs = getWeekdaysCheckboxes()
    inputs.forEach(x => x.disabled = !state)
}

function getWeekdaysCheckboxes() {
    return [... getWeekdaysSelectionElement()[0].getElementsByTagName('input')]
}

function beforeSubmit() {
    return validateForm()
}

function validateForm() {
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