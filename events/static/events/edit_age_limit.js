function getMinAgeField() {
    return document.getElementById('id_min_age')
}

function getMaxAgeField() {
    return document.getElementById('id_max_age')
}

function beforeSubmit() {
    return validateForm()
}

function validateForm() {
    const minAgeField = getMinAgeField()
    const maxAgeField = getMaxAgeField()
    const minAge = parseInt(minAgeField.value)
    const maxAge = parseInt(maxAgeField.value)

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
