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
    return validateWeekdaySelection()
}
