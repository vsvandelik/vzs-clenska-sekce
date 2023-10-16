window.addEventListener('load', event => {
    const checkboxes = [... document.getElementsByTagName('input')].filter(e => e.type === 'checkbox' && e.onchange !== null)
    for(const checkbox of checkboxes)
        organizerAttendaceChanged(checkbox)
})

function organizerAttendaceChanged(sender) {
    const idSplit = sender.id.split('_')
    const amountId = `${idSplit[0]}_${idSplit[1]}_amount`
    const amountElement = $(`#${amountId}`)
    amountElement.prop('disabled', !sender.checked)
}