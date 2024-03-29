// Variables
const days = ['po', 'ut', 'st', 'ct', 'pa', 'so', 'ne']


// Events
function dateChanged() {
    saveTrainingDaysStateToLocalStorage()
    validateDate()
    getSelectedDays().forEach(d => trainingDaysUpdate(d))
}

function timeChanged(sender) {
    validateTime(sender.name.split('_')[0])
}

function dayToggled(sender) {
    const day = sender.name
    saveTrainingDaysStateToLocalStorage()
    setTimeFieldsState(day, sender.checked)
    validateDay(true, sender)
    trainingDaysUpdate(day)
}

function trainingDayToggled(sender) {
    const day = sender.parentElement.parentElement.parentElement.parentElement.id.split('_')[1]
    if (sender.checked) {
        localStorage.removeItem(sender.value)
        clearCustomValidityFromTrainingDayElementsOf(day)
    } else {
        localStorage.setItem(sender.value, '0')
        const checkedCount = countCheckedTrainingDaysOf(day)
        if (checkedCount === 0)
            setReportValidity(sender, 'Alespoň jeden trénink se musí konat ve vybraný den pro pravidelné opakování', true)
    }
}

function beforeSubmit() {
    return validateForm()
}

window.onload = function () {
    dateChanged()
    getUnselectedDays().forEach(d => setTimeFieldsState(d, false))
    getSelectedDayElements().forEach(d => dayToggled(d))
}

window.onbeforeunload = function () {
    localStorage.clear()
}


// Validators
function validateDate(report = false) {
    const startsDate = document.getElementById('id_date_start')
    const endsDate = document.getElementById('id_date_end')
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

function validateDay(report = false, dayElement = getFirstDay(true)) {
    const noDayError = 'Není vybrán žádný den pro pravidelné opakování'
    if (dayElement === undefined) {
        dayElement = getFirstDay(false)
        setReportValidity(dayElement, noDayError, report)
        return false
    }
    const selectedCount = countSelectedDays()
    if (selectedCount > 3) {
        setReportValidity(dayElement, 'Překročen maximální počet konání 3x týdně', report)
        return false
    } else if (selectedCount === 0) {
        setReportValidity(dayElement, noDayError, report)
        return false
    } else {
        getAllDays().forEach(el => setReportValidity(el, '', report))
        return true
    }
}

function validateTime(day, report = false) {
    const fromId = `id_${day}_from`
    const toId = `id_${day}_to`
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
    return getSelectedDays().map(d => validateTime(d, report)).every(b => b === true)
}

function validateTrainingDay(day, report = false) {
    const daySelectedTrainings = countCheckedTrainingDaysOf(day)
    if (daySelectedTrainings === 0) {
        const trainingDay = getFirstUncheckedTrainingDay(day)
        setReportValidity(trainingDay, 'Alespoň jeden trénink se musí konat ve vybraný den pro pravidelné opakování', report)
        return false
    } else {
        clearCustomValidityFromTrainingDayElementsOf(day)
        return true
    }
}

function validateAllTrainingDaysDates(report = false) {
    const startsDateObj = getDateNulledHours(document.getElementById('id_date_start'))
    const endsDateObj = getDateNulledHours(document.getElementById('id_date_end'))
    for (const day of getSelectedDays()) {
        const weekday = dayShortToWeekday(day)
        const trainingDayElements = getTrainingDayElements(day)
        for (const element of trainingDayElements) {
            const date = parseCzechDate(element.value)
            if (date.getDay() !== weekday
                || date.getTime() < startsDateObj.getTime()
                || date.getTime() > endsDateObj.getTime()) {
                    setReportValidity(element, 'Neplatné datum tréninku', report)
                    return false
                }
        }
    }
    return true
}

function validateAllTrainingDays(report = false) {
    return getSelectedDays().map(d => validateTrainingDay(d, report)).every(b => b === true)
}

function validateForm() {
    return validateDate(true) && validateDay(true) && validateAllTimes(true) && validateAllTrainingDays(true) && validateAllTrainingDaysDates(true)
}

// Helper functions
function getDateNulledHours(element) {
    const date = convertCzechDate(element.value)
    date.setHours(0)
    return date
}

function getSelectedDays() {
    return days.filter(d => document.getElementById(`id_${d}`).checked)
}

function getUnselectedDays() {
    return days.filter(d => !document.getElementById(`id_${d}`).checked)
}

function getTrainingDayElements(day) {
    return [...document.getElementById(`id_${day}_tbody`).getElementsByTagName('input')]
}

function getAllTrainingDayElements() {
    return days.map(d => getTrainingDayElements(d)).flat()
}

function getAllDays() {
    return days.map(d => document.getElementById(`id_${d}`))
}

function getSelectedDayElements() {
    return getSelectedDays().map(d => document.getElementById(`id_${d}`))
}

function getFirstDay(checkedStatus) {
    const d = days.find(d => document.getElementById(`id_${d}`).checked === checkedStatus)
    if (d !== undefined)
        return document.getElementById(`id_${d}`)
    return undefined
}

function getFirstUncheckedTrainingDay(day) {
    const uncheckedTrainingDays = getTrainingDayElements(day).filter(e => !e.checked)
    if (uncheckedTrainingDays.length > 0)
        return uncheckedTrainingDays[0]
    return undefined
}

function saveTrainingDaysStateToLocalStorage() {
    const trainingDayElements = getAllTrainingDayElements()
    for (const element of trainingDayElements) {
        if (!element.checked)
            localStorage.setItem(element.value, '0')
    }
}

function trainingDaysUpdate(day) {
    const dayElement = document.getElementById(`id_${day}`)
    if (dayElement.checked && window._datesValid) {
        removeTrainingDays(day)
        setTimeFieldsState(day, true)
        addTrainingDaysTo(document.getElementById(`id_${day}_tbody`))
    } else {
        setTimeFieldsState(day, false)
        removeTrainingDays(day)
    }
}


function addTrainingDaysTo(parent) {
    const startsDate = getDateNulledHours(document.getElementById('id_date_start'))
    const endsDate = getDateNulledHours(document.getElementById('id_date_end'))
    const day = parent.id.split('_')[1]
    moveDaysToFirstTraining(startsDate, day)
    while (endsDate >= startsDate) {
        const datePretty = formatCzechDate(startsDate)
        const tr = createCheckboxWithLabel('day', datePretty, datePretty)
        parent.appendChild(tr)
        startsDate.setDate(startsDate.getDate() + 7)
    }
}

function setTimeFieldsState(day, state) {
    const display = state ? 'block' : 'none'
    const time_from = document.getElementById(`id_${day}_from`)
    const time_to = document.getElementById(`id_${day}_to`)
    time_from.required = state
    time_to.required = state
    const parent = document.getElementById(`id_${day}_from`).parentElement.parentElement.parentElement.parentElement.parentElement
    parent.style.display = display
    const fields = parent.getElementsByTagName('input')
    fields[0].disabled = !state
    fields[1].disabled = !state
}

function createCheckboxWithLabel(name, value, labelTxt) {
    const checkbox = document.createElement('input')
    checkbox.type = 'checkbox'
    checkbox.name = name
    checkbox.value = value
    checkbox.id = value
    checkbox.classList.add('custom-control-input')
    checkbox.checked = localStorage.getItem(value) === null
    checkbox.addEventListener('change', () =>
        trainingDayToggled(checkbox), false)

    const label = document.createElement('label')
    label.htmlFor = value
    label.style.paddingLeft = '3px'
    label.classList.add('font-weight-normal', 'custom-control-label')

    const txtNode = document.createTextNode(labelTxt)
    label.appendChild(txtNode)

    const div = document.createElement('div')
    div.classList.add('custom-control', 'custom-checkbox')
    div.appendChild(checkbox)
    div.appendChild(label)

    const td = document.createElement('td')
    td.classList.add('w-100')
    td.appendChild(div)

    const tr = document.createElement('tr')
    tr.appendChild(td)

    return tr
}

function countCheckedTrainingDaysOf(day) {
    return getTrainingDayElements(day).filter(e => e.checked).length
}

function clearCustomValidityFromTrainingDayElementsOf(day) {
    getTrainingDayElements(day).forEach(e => setReportValidity(e, '', true))
}

function moveDaysToFirstTraining(date, day) {
    day = dayShortToWeekday(day)
    while (date.getDay() !== day)
        date.setDate(date.getDate() + 1)
}

function dayShortToWeekday(dayShort) {
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

function removeTrainingDays(day) {
    document.getElementById(`id_${day}_tbody`).innerHTML = ''
}

function countSelectedDays() {
    return getSelectedDays().length
}
