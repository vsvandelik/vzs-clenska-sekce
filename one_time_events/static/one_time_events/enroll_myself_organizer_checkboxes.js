function notifyCheckboxDisable(checkbox) {
    checkbox.prop('disabled', true)
    checkbox.prop('checked', false)
}

function notifyCheckboxEnable(checkbox) {
    checkbox.prop('disabled', false)
    checkbox.prop('checked', true)
}