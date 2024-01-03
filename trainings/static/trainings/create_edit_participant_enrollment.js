window.addEventListener('load', event => {
    $('form').on('submit', beforeSubmit)
    stateChanged()
})

function stateChanged() {
    const newValue = getStateElement().value
    const weekdaysSelectionElement = getWeekdaysSelectionElement()
    if(newValue === 'schvalen' || newValue === 'nahradnik')
        weekdaysSelectionElement.show()

    else {
        weekdaysSelectionElement.hide()
        const firstCheckbox = weekdaysSelectionElement[0].getElementsByTagName('input')[0]
        firstCheckbox.checked = true
    }

}

function beforeSubmit() {
    return validateWeekdaySelection()
}
