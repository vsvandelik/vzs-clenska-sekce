window.onload = function () {
    minAgeCheckboxClicked(getMinAgeCheckbox())
}

function minAgeCheckboxClicked(sender) {
    const minAgeField = getMinAgeField()
    minAgeField.disabled = !sender.checked
    setElementRequired(minAgeField, sender.checked)
}

function getMinAgeCheckbox() {
    return document.getElementById('id_min_age_enabled')
}
function getMinAgeField() {
    return document.getElementById('id_min_age')
}
function beforeSubmit() {
    return validateForm()
}

function validateForm() {
    const minAgeField = getMinAgeField()
    let minAge
    if (getMinAgeCheckbox().checked)
        minAge = parseInt(minAgeField.value)

    if (minAge !== undefined) {
        if (minAge < 1 || minAge > 99) {
            setReportValidity(minAgeField, 'Hodnota minimální věkové hranice musí být mezi 1 a 99')
            return false
        }
    }
    setReportValidity(minAgeField, '', true)
    return true
}
