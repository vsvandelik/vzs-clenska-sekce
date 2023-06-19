const days = ['po', 'ut', 'st', 'ct', 'pa', 'so', 'ne']


function dateChanged() {
    validateDate()

    const selectedDays = days.filter(d => document.getElementById(`id_${d}`).checked)
    selectedDays.forEach(d => checkTrainingDays(document.getElementById(`id_${d}`)))

}

function getDateNulledHours(element) {
    const date = new Date(element.value)
    date.setHours(0)
    return date
}

function validateDate() {
    const starts_date = document.getElementById('id_starts_date')
    const ends_date = document.getElementById('id_ends_date')
    const starts_date_obj = getDateNulledHours(starts_date)
    const ends_date_obj = getDateNulledHours(ends_date)
    const secondsBetween = (ends_date_obj.getTime() - starts_date_obj.getTime()) / 1000
    const secondsInWeek = 604800
    if (secondsBetween < secondsInWeek * 2 || isNaN(secondsBetween)) {
        window._datesValid = false
        ends_date.setCustomValidity('Pravidelná událost se koná alespoň 2 týdny')
    } else {
        window._datesValid = true
        ends_date.setCustomValidity('')
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

function dayToggled(element) {
    displayTimeSettingForDay(element)
    checkTrainingDaysOfTheWeekChosen()
    checkTrainingDays(element)

}

function checkTrainingDays(element) {
    const daysFieldsetId = `${element.id}_days`
    const daysFieldset = document.getElementById(daysFieldsetId)
    if (element.checked && window._datesValid) {
        removeChildrenAfterLegend(daysFieldset)
        daysFieldset.style.display = 'block'
        addCheckedDateCheckboxesTo(daysFieldset)
    } else {
        daysFieldset.style.display = 'none'
        removeChildrenAfterLegend(daysFieldset)
    }
}

function addCheckedDateCheckboxesTo(daysFieldset) {
    const starts_date = getDateNulledHours(document.getElementById('id_starts_date'))
    const ends_date = getDateNulledHours(document.getElementById('id_ends_date'))
    moveDaysToFirstTraining(starts_date, daysFieldset)
    while (ends_date.getTime() >= starts_date.getTime()) {
        const datePretty = formatCzechDate(starts_date)
        const [checkbox, label] =
            createCheckboxWithLabel('day', datePretty, datePretty)
        daysFieldset.appendChild(checkbox)
        daysFieldset.appendChild(label)
        starts_date.setDate(starts_date.getDate() + 7)
    }
}

function formatCzechDate(date) {
    return `${date.getDate()}.${date.getMonth() + 1}.${date.getFullYear()}`
}

function parseCzechDate(date_str) {
    const [day, month, year] = date_str.split('.')
    return new Date(year, month - 1, day, 0, 0, 0, 0)
}

function createCheckboxWithLabel(name, value, labelTxt) {
    const checkbox = document.createElement('input')
    checkbox.type = 'checkbox'
    checkbox.name = name
    checkbox.value = value
    checkbox.id = value
    checkbox.checked = true
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
        for (let i = 0; i < parentFieldset.childNodes.length; ++i) {
            if (parentFieldset.childNodes[i].nodeName.toLowerCase() === 'input')
                parentFieldset.childNodes[i].disabled = false
        }
    } else {
        const checkedCount = countCheckedCheckboxesIn(parentFieldset)
        if (checkedCount === 1) {
            for (let i = 0; i < parentFieldset.childNodes.length; ++i) {
                if (parentFieldset.childNodes[i].nodeName.toLowerCase() === 'input'
                    && parentFieldset.childNodes[i].checked)
                    parentFieldset.childNodes[i].disabled = true
            }
        }
    }
}

function countCheckedCheckboxesIn(parentElement) {
    let counter = 0
    for (let i = 0; i < parentElement.childNodes.length; ++i) {
        if (parentElement.childNodes[i].nodeName.toLowerCase() === 'input'
            && parentElement.childNodes[i].type === 'checkbox'
            && parentElement.childNodes[i].checked)
            ++counter
    }
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
    for (let i = 0; i < parentElement.childNodes.length; ++i) {
        if (parentElement.childNodes[i].nodeName.toLowerCase() === 'input'
            && parentElement.childNodes[i].type === 'checkbox')
            parentElement.childNodes[i].setCustomValidity('')
    }
}

function moveDaysToFirstTraining(date, daysFieldset) {
    let day = daysFieldset.id.substring(3, 5)
    day = day_short_2_day_of_week(day)
    while (date.getDay() !== day)
        date.setDate(date.getDate() + 1)
}

function day_short_2_day_of_week(day_short) {
    if (day_short === 'ne')
        return 0
    else if (day_short === 'po')
    return 1
    else if (day_short === 'ut')
    return 2
    else if (day_short === 'st')
    return 3
    else if (day_short === 'ct')
    return 4
    else if (day_short === 'pa')
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

function checkTrainingDaysOfTheWeekChosen() {
    const shouldChoose = getTrainingsPerWeekValue()
    const chosenCount = countChosenDays()
    if (shouldChoose === chosenCount)
        setStateAllDays(false)
    else
        setStateAllDays(true)
}

function trainingsPerWeekChanged() {
    let trainings = getTrainingsPerWeekValue()
    let chosenCount = countChosenDays()
    const rDays = days.reverse()
    while (trainings < chosenCount) {
        const idToUncheck = rDays.find(d => document.getElementById(`id_${d}`).checked)
        document.getElementById(`id_${idToUncheck}`).click()
        --chosenCount
    }
    checkTrainingDaysOfTheWeekChosen()
}

function countChosenDays() {
    return days.filter(d => document.getElementById(`id_${d}`).checked).length
}

function displayTimeSettingForDay(element) {
    const newdisplay = element.checked ? 'block' : 'none'
    const daytimeid = `${element.id}_time`
    const daytime = document.getElementById(daytimeid)
    daytime.style.display = newdisplay
    setStateFromToFields(element.id, !element.checked)
}

function setStateFromToFields(id, state) {
    const day_shortcut = id.split('_')[1]
    const f1id = `id_from_${day_shortcut}`
    const f2id = `id_to_${day_shortcut}`
    document.getElementById(f1id).disabled = state
    document.getElementById(f2id).disabled = state
}

function setStateAllDays(state) {
    days.filter(d => !document.getElementById(`id_${d}`).checked)
        .forEach(d => document.getElementById(`id_${d}`).disabled = !state)
}

function checkChosenDaysValid() {
    const starts_date_obj = getDateNulledHours(document.getElementById('id_starts_date'))
    const ends_date_obj = getDateNulledHours(document.getElementById('id_ends_date'))
    const chosenDays = days.filter(d => document.getElementById(`id_${d}`).checked)
    const parentFieldsets = chosenDays.map(d => document.getElementById(`id_${d}_days`))
    for (const fieldset of parentFieldsets) {
        const weekday = day_short_2_day_of_week(fieldset.id.split('_')[1])
        for (const child of fieldset.childNodes) {
            if (child.nodeName.toLowerCase() === 'input'
                && child.type === 'checkbox'
                && child.checked) {
                    const date = parseCzechDate(child.value)
                    if (date.getDay() !== weekday
                        || date.getTime() < starts_date_obj.getTime()
                        || date.getTime() > ends_date_obj.getTime()) {
                            child.setCustomValidity('Neplatné datum tréninku')
                            return false
                        }
                }
        }
    }
    return true
}

function enableDayCheckboxes() {
    const parentFieldsets = days.map(d => document.getElementById(`id_${d}_days`))
    for (const fieldset of parentFieldsets) {
        for (const child of fieldset.childNodes) {
            if (child.nodeName.toLowerCase() === 'input' && child.type === 'checkbox') {
                child.disabled = false
            }
        }
    }
}

function validateForm() {
    const trainingsPerWeek = getTrainingsPerWeekValue()
    const daysInWeekFieldset = document.getElementById('id_days_in_week')
    const firstUnchecked = getFirstUncheckedCheckboxIn(daysInWeekFieldset)
    const selectedDaysPerWeek = countCheckedCheckboxesIn(daysInWeekFieldset)

    if (!checkChosenDaysValid())
        return false

    if (trainingsPerWeek !== selectedDaysPerWeek) {
        firstUnchecked.setCustomValidity('Není vybrán odpovídající počet dní v týdnu vzhledem k počtu tréninků')
        return false
    }
    clearCustomValidityFromAllCheckboxesIn(daysInWeekFieldset)
    enableDayCheckboxes()
    return true
}

window.onload = function () {
    validateDate()
    trainingsPerWeekChanged()

    if(document.getElementById('training_header').innerText.startsWith('Nový')) {
        const checkedDays = days.filter(d => document.getElementById(`id_${d}`).checked)
        checkedDays.forEach(d => checkTrainingDays(document.getElementById(`id_${d}`)))
    }
}