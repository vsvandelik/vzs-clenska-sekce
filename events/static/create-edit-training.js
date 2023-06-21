// Variables
const days = ['po', 'ut', 'st', 'ct', 'pa', 'so', 'ne']


// Events
function dateChanged() {
    saveCheckboxesToLocalStorage()
    validateDate()
    getSelectedDays().forEach(d => trainingDaysUpdate(document.getElementById(`id_${d}`)))
}

function dowTimeChanged(sender) {
    validateDowTime(sender.id.split('_')[2])
}

function dowToggled(sender) {
    saveCheckboxesOfParentToLocalStorage(document.getElementById(`${sender.id}_days`))
    setTimeVisibilityForDowElement(sender)
    validateDow(true, sender)
    trainingDaysUpdate(sender)
}

function beforeSubmit() {
    if (validateForm()) {
        enableAllTrainingDaysCheckboxes()
        return true
    }
    return false
}

window.onload = function () {
    dateChanged()
    getSelectedDow().forEach(d => dowToggled(d))
}

window.onbeforeunload = function () {
    localStorage.clear()
};


// Validators
function validateDate(report = false) {
    const startsDate = document.getElementById('id_starts_date')
    const endsDate = document.getElementById('id_ends_date')
    const startsDateObj = getDateNulledHours(startsDate)
    const endsDateObj = getDateNulledHours(endsDate)
    const secondsBetween = (endsDateObj.getTime() - startsDateObj.getTime()) / 1000
    const secondsInWeek = 604800
    if (secondsBetween < secondsInWeek * 2 || isNaN(secondsBetween)) {
        window._datesValid = false
        setReportValidity(endsDate, 'Pravidelná událost se koná alespoň 2 týdny', report)
        return false
    } else {
        window._datesValid = true
        setReportValidity(endsDate, '', report)
        return true
    }
}

function validateDow(report = false, dowElement = getFirstDow(true)) {
    const noDayError = 'Není vybrán žádný den pro pravidelné opakování'
    if (dowElement === undefined) {
        dowElement = getFirstDow(false)
        setReportValidity(dowElement, noDayError, report)
        return false
    }
    const selectedCount = countSelectedDays()
    if (selectedCount > 3) {
        setReportValidity(dowElement, 'Překročen maximální počet konání 3x týdně', report)
        return false
    } else if (selectedCount === 0) {
        setReportValidity(dowElement, noDayError, report)
        return false
    } else {
        getAllDow().forEach(el => setReportValidity(el, '', report))
        return true
    }
}

function validateDowTime(day, report = false) {
    const fromId = `id_from_${day}`
    const toId = `id_to_${day}`
    const fromElm = document.getElementById(fromId)
    const toElm = document.getElementById(toId)
    const fromVal = fromElm.value
    const [fromHour, fromMinute] = fromVal.split(':')
    const toVal = toElm.value
    const [toHour, toMinute] = toVal.split(':')
    if (fromHour < toHour || (fromHour <= toHour && fromMinute < toMinute)) {
        setReportValidity(toElm, '', report)
        return true
    } else {
        setReportValidity(toElm, 'Konec tréningu je čas před jeho začátkem', report)
        return false
    }
}

function validateAllTimes(report = false) {
    return getSelectedDays().map(d => validateDowTime(d, report)).every(b => b === true)
}

function validateTrainingDay(day, report = false) {
    const parentElement = document.getElementById(`id_${day}_days`)
    const daySelectedTrainings = countCheckedCheckboxesIn(parentElement)
    if (daySelectedTrainings === 0) {
        const trainingDay = getFirstUncheckedTrainingDay(parentElement)
        setReportValidity(trainingDay, 'Alespoň jeden trénink se musí konat ve vybraný den pro pravidelné opakování', report)
        return false
    } else {

        clearCustomValidityFromAllCheckboxesIn(parentElement)
        return true
    }
}

function validateAllTrainingDaysDates(report = false) {
    const startsDateObj = getDateNulledHours(document.getElementById('id_starts_date'))
    const endsDateObj = getDateNulledHours(document.getElementById('id_ends_date'))
    const parentFieldsets = getParentElementsOfSelectedDow()
    for (const fieldset of parentFieldsets) {
        const weekday = dayShort2dow(fieldset.id.split('_')[1])
        for (const child of fieldset.childNodes) {
            if (child.nodeName.toLowerCase() === 'input'
                && child.type === 'checkbox'
                && child.checked) {
                    const date = parseCzechDate(child.value)
                    if (date.getDay() !== weekday
                        || date.getTime() < startsDateObj.getTime()
                        || date.getTime() > endsDateObj.getTime()) {
                            setReportValidity(child, 'Neplatné datum tréninku', report)
                            return false
                        }
                }
        }
    }
    return true
}

function validateAllTrainingDays(report = false) {
    return getSelectedDays().map(d => validateTrainingDay(d, report)).every(b => b === true)
}

function validateForm() {
    return validateDate(true) && validateDow(true) && validateAllTimes(true) && validateAllTrainingDays(true) && validateAllTrainingDaysDates(true)
}

// Helper functions
function getDateNulledHours(element) {
    const date = new Date(element.value)
    date.setHours(0)
    return date
}

function saveCheckboxesOfParentToLocalStorage(parent) {
    applyToCheckboxesOfParent(parent, child => {
        if (!child.checked)
            localStorage.setItem(child.value, '0')
    })
}

function getSelectedDays() {
    return days.filter(d => document.getElementById(`id_${d}`).checked)
}

function getParentElementsOfSelectedDow() {
    return getSelectedDays().map(d => document.getElementById(`id_${d}_days`))
}

function getAllDow() {
    return days.map(d => document.getElementById(`id_${d}`))
}

function getSelectedDow() {
    return getSelectedDays().map(d => document.getElementById(`id_${d}`))
}

function getFirstDow(checkedStatus) {
    const d = days.find(d => document.getElementById(`id_${d}`).checked === checkedStatus)
    if (d !== undefined)
        return document.getElementById(`id_${d}`)
    return undefined
}

function getFirstUncheckedTrainingDay(parentElement) {
    for (const child of parent.childNodes) {
        if (child.nodeName.toLowerCase() === 'input' && child.type === 'checkbox' && !child.checked)
            return child
    }
    return undefined
}

function saveCheckboxesToLocalStorage() {
    const parentFieldsets = getParentElementsOfSelectedDow()
    for (const fieldset of parentFieldsets)
        saveCheckboxesOfParentToLocalStorage(fieldset)
}

function applyToCheckboxesOfParent(parent, func) {
    for (const child of parent.childNodes) {
        if (child.nodeName.toLowerCase() === 'input' && child.type === 'checkbox') {
            func(child)
        }
    }
}

function trainingDaysUpdate(dowElement) {
    const daysFieldsetId = `${dowElement.id}_days`
    const daysFieldset = document.getElementById(daysFieldsetId)
    if (dowElement.checked && window._datesValid) {
        removeChildrenAfterLegend(daysFieldset)
        daysFieldset.style.display = 'block'
        addDateCheckboxesTo(daysFieldset)
    } else {
        daysFieldset.style.display = 'none'
        removeChildrenAfterLegend(daysFieldset)
    }
}

function addDateCheckboxesTo(daysFieldset) {
    const startsDate = getDateNulledHours(document.getElementById('id_starts_date'))
    const endsDate = getDateNulledHours(document.getElementById('id_ends_date'))
    moveDaysToFirstTraining(startsDate, daysFieldset)
    while (endsDate.getTime() >= startsDate.getTime()) {
        const datePretty = formatCzechDate(startsDate)
        const [checkbox, label] =
            createCheckboxWithLabel('day', datePretty, datePretty)
        daysFieldset.appendChild(checkbox)
        daysFieldset.appendChild(label)
        startsDate.setDate(startsDate.getDate() + 7)
    }
}

function formatCzechDate(date) {
    return `${date.getDate()}.${date.getMonth() + 1}.${date.getFullYear()}`
}

function parseCzechDate(dateStr) {
    const [day, month, year] = dateStr.split('.')
    return new Date(year, month - 1, day, 0, 0, 0, 0)
}

function createCheckboxWithLabel(name, value, labelTxt) {
    const checkbox = document.createElement('input')
    checkbox.type = 'checkbox'
    checkbox.name = name
    checkbox.value = value
    checkbox.id = value
    checkbox.checked = localStorage.getItem(value) === null
    checkbox.addEventListener('change', () =>
        trainingDayToggled(checkbox), false)

    const label = document.createElement('label')
    label.htmlFor = value
    const txtNode = document.createTextNode(labelTxt)
    label.appendChild(txtNode)

    return [checkbox, label]
}

function trainingDayToggled(sender) {
    const parentFieldset = sender.parentElement
    if (sender.checked) {
        localStorage.removeItem(sender.value)
        clearCustomValidityFromAllCheckboxesIn(parentFieldset)
    } else {
        localStorage.setItem(sender.value, '0')
        const checkedCount = countCheckedCheckboxesIn(parentFieldset)
        if (checkedCount === 0)
            setReportValidity(sender, 'Alespoň jeden trénink se musí konat ve vybraný den pro pravidelné opakování', true)
    }
}

function countCheckedCheckboxesIn(parentElement) {
    let counter = 0
    applyToCheckboxesOfParent(parentElement, child => {
        if (child.checked)
            ++counter
    })
    return counter
}

function clearCustomValidityFromAllCheckboxesIn(parentElement) {
    applyToCheckboxesOfParent(parentElement, child => setReportValidity(child, '', true))
}

function moveDaysToFirstTraining(date, daysFieldset) {
    let day = daysFieldset.id.substring(3, 5)
    day = dayShort2dow(day)
    while (date.getDay() !== day)
        date.setDate(date.getDate() + 1)
}

function dayShort2dow(dayShort) {
    if (dayShort === 'ne')
        return 0
    else if (dayShort === 'po')
    return 1
    else if (dayShort === 'ut')
    return 2
    else if (dayShort === 'st')
    return 3
    else if (dayShort === 'ct')
    return 4
    else if (dayShort === 'pa')
    return 5
    else
        return 6
}

function removeChildrenAfterLegend(element) {
    while (element.childNodes.length > 1
        && element.lastChild.nodeName.toLowerCase() !== 'legend')
        element.removeChild(element.lastChild);

}


function countSelectedDays() {
    return getSelectedDays().length
}

function setTimeVisibilityForDowElement(dowElement) {
    const newdisplay = dowElement.checked ? 'block' : 'none'
    const daytimeid = `${dowElement.id}_time`
    const daytime = document.getElementById(daytimeid)
    daytime.style.display = newdisplay
    setTimeFieldsState(dowElement.id.split('_')[1], !dowElement.checked)
}

function setTimeFieldsState(day, state) {
    const f1id = `id_from_${day}`
    const f2id = `id_to_${day}`
    document.getElementById(f1id).disabled = state
    document.getElementById(f2id).disabled = state
}

function enableAllTrainingDaysCheckboxes() {
    const parentFieldsets = getParentElementsOfSelectedDow()
    for (const fieldset of parentFieldsets) {
        applyToCheckboxesOfParent(fieldset, child => child.disabled = false)
    }
}

function setReportValidity(object, txt, report = false) {
    object.setCustomValidity(txt)
    if (report)
        object.reportValidity()
}