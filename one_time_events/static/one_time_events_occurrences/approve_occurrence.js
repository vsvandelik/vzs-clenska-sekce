function organizerAttendaceChanged(sender) {
    const idSplit = sender.id.split('_')
    const amountId = `${idSplit[0]}_${idSplit[1]}_amount`
    const amountElement = $(`#${amountId}`)
    amountElement.prop('disabled', !amountElement.attr('disabled'))
}