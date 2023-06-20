const days = ['po', 'ut', 'st', 'ct', 'pa', 'so', 'ne']

// const pageAccessedByReload = (
//   (window.performance.navigation && window.performance.navigation.type === 1) ||
//     window.performance
//       .getEntriesByType('navigation')
//       .map(nav => nav.type)
//       .includes('reload')
// );

function dateChanged() {
    validateDate()
    const selectedDays = getSelectedDays()
    selectedDays.forEach(d => trainingDaysUpdate(document.getElementById(`id_${d}`)))
}

function getDateNulledHours(element) {
    const date = new Date(element.value)
    date.setHours(0)
    return date
}

function validateDate() {
    const startsDate = document.getElementById('id_starts_date')
    const endsDate = document.getElementById('id_ends_date')
    const startsDateObj = getDateNulledHours(startsDate)
    const endsDateObj = getDateNulledHours(endsDate)
    const secondsBetween = (endsDateObj.getTime() - startsDateObj.getTime()) / 1000
    const secondsInWeek = 604800
    if (secondsBetween < secondsInWeek * 2 || isNaN(secondsBetween)) {
        window._datesValid = false
        endsDate.setCustomValidity('Pravidelná událost se koná alespoň 2 týdny')
    } else {
        window._datesValid = true
        endsDate.setCustomValidity('')
    }
}

function validateTimes(sender) {
    const day = sender.id.split('_')[2]
    const fromId = `id_from_${day}`
    const toId = `id_to_${day}`
    const fromElm = document.getElementById(fromId)
    const toElm = document.getElementById(toId)
    const fromVal = fromElm.value
    const [fromHour, fromMinute] = fromVal.split(':')
    const toVal = toElm.value
    const [toHour, toMinute] = toVal.split(':')
    if (fromHour < toHour || (fromHour <= toHour && fromMinute < toMinute)) {
        toElm.setCustomValidity('')
        return true
    } else {
        toElm.setCustomValidity('Konec tréningu je čas před jeho začátkem')
        return false
    }

}

function dowToggled(sender) {
    saveCheckboxesOfParentToLocalStorage(document.getElementById(`${sender.id}_days`))
    setDisplayTimeSettingForDay(sender)
    dowUpdate()
    trainingDaysUpdate(sender)

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

function getUnselectedDays() {
    return days.filter(d => !document.getElementById(`id_${d}`).checked)
}

function getParentFieldsetsOfSelectedDow() {
    return getSelectedDays().map(d => document.getElementById(`id_${d}_days`))

}

function saveCheckboxesToLocalStorage() {
    const parentFieldsets = getParentFieldsetsOfSelectedDow()
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
    if (countCheckedCheckboxesIn(daysFieldset) === 1)
        disableCheckedCheckboxesInParent(daysFieldset)
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
        applyToCheckboxesOfParent(parentFieldset, child => child.disabled = false)
    } else {
        localStorage.setItem(sender.value, '0')
        const checkedCount = countCheckedCheckboxesIn(parentFieldset)
        if (checkedCount === 1)
            disableCheckedCheckboxesInParent(parentFieldset)
    }
}

function disableCheckedCheckboxesInParent(parent) {
    applyToCheckboxesOfParent(parent, child => {
        if (child.checked)
            child.disabled = true
    })
}

function countCheckedCheckboxesIn(parentElement) {
    let counter = 0
    applyToCheckboxesOfParent(parentElement, child => {
        if (child.checked)
            ++counter
    })
    return counter
}

function getFirstUncheckedCheckboxIn(parentElement) {
    for (let i = 0; i < parentElement.childNodes.length; ++i) {
        if (parentElement.childNodes[i].nodeName.toLowerCase() === 'input'
            && parentElement.childNodes[i].type === 'checkbox'
            && !parentElement.childNodes[i].checked)
            return parentElement.childNodes[i]
    }
    return undefined
}

function clearCustomValidityFromAllCheckboxesIn(parentElement) {
    applyToCheckboxesOfParent(parentElement, child => child.setCustomValidity(''))
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

function getTrainingsPerWeekValue() {
    return parseInt(document.getElementById('id_trainings_per_week').value)
}

function dowUpdate() {
    const shouldChoose = getTrainingsPerWeekValue()
    const chosenCount = countSelectedDays()
    if (shouldChoose === chosenCount)
        setStateUncheckedDow(false)
    else
        setStateUncheckedDow(true)
}

function trainingsPerWeekChanged() {
    let trainings = getTrainingsPerWeekValue()
    let chosenCount = countSelectedDays()
    const rDays = days.reverse()
    while (trainings < chosenCount) {
        const idToUncheck = rDays.find(d => document.getElementById(`id_${d}`).checked)
        document.getElementById(`id_${idToUncheck}`).click()
        --chosenCount
    }
    dowUpdate()
}

function countSelectedDays() {
    return getSelectedDays().length
}

function setDisplayTimeSettingForDay(dowElement) {
    const newdisplay = dowElement.checked ? 'block' : 'none'
    const daytimeid = `${dowElement.id}_time`
    const daytime = document.getElementById(daytimeid)
    daytime.style.display = newdisplay
    setStateFromToFields(dowElement.id, !dowElement.checked)
}

function setStateFromToFields(id, state) {
    const dayShortcut = id.split('_')[1]
    const f1id = `id_from_${dayShortcut}`
    const f2id = `id_to_${dayShortcut}`
    document.getElementById(f1id).disabled = state
    document.getElementById(f2id).disabled = state
}

function setStateUncheckedDow(state) {
    getUnselectedDays().forEach(d => document.getElementById(`id_${d}`).disabled = !state)
}

function checkSelectedDaysValid() {
    const startsDateObj = getDateNulledHours(document.getElementById('id_starts_date'))
    const endsDateObj = getDateNulledHours(document.getElementById('id_ends_date'))
    const parentFieldsets = getParentFieldsetsOfSelectedDow()
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
                            child.setCustomValidity('Neplatné datum tréninku')
                            return false
                        }
                }
        }
    }
    return true
}

function enableAllTrainingDaysCheckboxes() {
    const parentFieldsets = getParentFieldsetsOfSelectedDow()
    for (const fieldset of parentFieldsets) {
        applyToCheckboxesOfParent(fieldset, child => child.disabled = false)
    }
}

function validateForm() {
    const trainingsPerWeek = getTrainingsPerWeekValue()
    const daysInWeekFieldset = document.getElementById('id_days_in_week')
    const firstUnchecked = getFirstUncheckedCheckboxIn(daysInWeekFieldset)
    const selectedDaysPerWeek = countCheckedCheckboxesIn(daysInWeekFieldset)

    if (!checkSelectedDaysValid())
        return false

    if (trainingsPerWeek !== selectedDaysPerWeek) {
        firstUnchecked.setCustomValidity('Není vybrán odpovídající počet dní v týdnu vzhledem k počtu tréninků')
        return false
    }
    clearCustomValidityFromAllCheckboxesIn(daysInWeekFieldset)
    return true
}

function beforeSubmit() {
    if (validateForm()) {
        saveCheckboxesToLocalStorage()
        enableAllTrainingDaysCheckboxes()
        return true
    }
    return false
}

window.onbeforeunload = function(e) {
    saveCheckboxesToLocalStorage()
};

function isNewEvent() {
    return document.getElementById('training_header').innerText.startsWith('Nový')
}

window.onload = function () {
    if(!isNewEvent())
        localStorage.clear()

    //const editPageWithoutReload = selectedDaysCount > 0 && !pageAccessedByReload
    // if(editPageWithoutReload)
    //     localStorage.clear()

    validateDate()
    trainingsPerWeekChanged()

    if(isNewEvent())
        getSelectedDays().forEach(d => trainingDaysUpdate(document.getElementById(`id_${d}`)))

    localStorage.clear()
}