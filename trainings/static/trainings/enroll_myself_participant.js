window.addEventListener('load', event => {
    $('form').on('submit', beforeSubmit)
})

function beforeSubmit() {
    return validateWeekdaySelection()
}