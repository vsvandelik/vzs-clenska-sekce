window.onload = function () {
    minAgeCheckboxClicked(getMinAgeCheckbox())
    maxAgeCheckboxClicked(getMaxAgeCheckbox())
}

function minAgeCheckboxClicked(sender) {
    const minAgeField = getMinAgeField()
    minAgeField.disabled = !sender.checked
    setRequired(minAgeField, sender.checked)
}

function maxAgeCheckboxClicked(sender) {
    const maxAgeField = getMaxAgeField()
    maxAgeField.disabled = !sender.checked
    setRequired(maxAgeField, sender.checked)
}

function getMinAgeCheckbox() {
    return document.getElementById('id_min_age_enabled')
}

function getMaxAgeCheckbox() {
    return document.getElementById('id_max_age_enabled')
}

function getMinAgeField() {
    return document.getElementById('id_min_age')
}

function getMaxAgeField() {
    return document.getElementById('id_max_age')
}

function setRequired(element, state) {
    element.required = state
    if (state) {
        if (element.labels[0].innerText.slice(-1) !== '*')
            element.labels[0].innerText += '*'
    } else {
        while (element.labels[0].innerText.slice(-1) === '*')
            element.labels[0].innerText = element.labels[0].innerText.slice(0, -1)
    }
}

function beforeSubmit() {
    return validateForm()
}

function validateForm() {
    const minAgeField = getMinAgeField()
    const maxAgeField = getMaxAgeField()
    let minAge, maxAge
    if (getMinAgeCheckbox().checked)
        minAge = parseInt(minAgeField.value)
    if (getMaxAgeCheckbox().checked)
        maxAge = parseInt(maxAgeField.value)

    if (minAge !== undefined && maxAge !== undefined) {
        if (minAge > maxAge) {
            setReportValidity(maxAgeField, 'Hodnota minimální věkové hranice musí být menší nebo rovna hodnotě maximální věkové hranice', true)
            return false
        }
    }
    if (minAge !== undefined) {
        if (minAge < 1 || minAge > 99) {
            setReportValidity(minAgeField, 'Hodnota minimální věkové hranice musí být mezi 1 a 99')
            return false
        }
    }
    if (maxAge !== undefined) {
        if (maxAge < 1 || maxAge > 99) {
            setReportValidity(maxAgeField, 'Hodnota maximální věkové hranice musí být mezi 1 a 99')
            return false
        }
    }
    setReportValidity(minAgeField, '', true)
    setReportValidity(maxAgeField, '', true)
    return true
}
