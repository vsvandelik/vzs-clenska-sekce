window.addEventListener('load', event => {
    $('form').on('submit', beforeSubmit)
    stateChanged()
})

function stateChanged() {
    const newValue = getStateElement().value
    const weekdaysSelectionElement = getWeekdaysSelectionElement()
    if(newValue === 'schvalen' || newValue === 'nahradnik')
        weekdaysSelectionElement.show()

    else
        weekdaysSelectionElement.hide()

}

function beforeSubmit() {
    return validateWeekdaySelection()
}
