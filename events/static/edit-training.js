const days = ['po', 'ut', 'st', 'ct', 'pa', 'so', 'ne']


function dateChanged() {
    validateDate()

    const selectedDays = days.filter(d => document.getElementById(d).checked)
    selectedDays.forEach(f => checkTrainingDays(document.getElementById(f)))

}

function validateDate() {
    const starts_date = document.getElementById('starts_date')
    const ends_date = document.getElementById('ends_date')
    const starts_date_obj = new Date(starts_date.value)
    const ends_date_obj = new Date(ends_date.value)
    const secondsBetween = (ends_date_obj.getTime() - starts_date_obj.getTime()) / 1000
    const secondsInWeek = 604800
    if (secondsBetween < secondsInWeek * 2 || isNaN(secondsBetween)) {
        window._datesValid = false
        ends_date.setCustomValidity('Pravidelná akce se koná alespoň 2 týdny')
    } else {
        window._datesValid = true
        ends_date.setCustomValidity('')
    }
}

function validateTimes(sender) {
    const day = sender.id.split('_')[1]
    const fromId = `from_${day}`
    const toId = `to_${day}`
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
    const starts_date = new Date(document.getElementById('starts_date').value)
    const ends_date = new Date(document.getElementById('ends_date').value)
    moveDaysToFirstTraining(starts_date, daysFieldset)
    while (ends_date.getTime() > starts_date.getTime()) {
        const datePretty = formatCzechDate(starts_date)
        const [checkbox, label] =
            createCheckboxWithLabel('day[]', datePretty, datePretty)
        daysFieldset.appendChild(checkbox)
        daysFieldset.appendChild(label)
        starts_date.setDate(starts_date.getDate() + 7)
    }
}

function formatCzechDate(date) {
    return `${date.getDate()}.${date.getMonth() + 1}.${date.getFullYear()}`
}

function createCheckboxWithLabel(name, value, labelTxt) {
    const checkbox = document.createElement('input')
    checkbox.type = 'checkbox'
    checkbox.name = name
    checkbox.value = value
    checkbox.id = value
    checkbox.checked = true
    checkbox.addEventListener('change', () => trainingDayToggled(checkbox), false)

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
            && parentElement.childNodes[i].type === 'checkbox' && parentElement.childNodes[i].checked)
            ++counter
    }
    return counter
}

function getFirstUncheckedCheckboxIn(parentElement) {
    for (let i = 0; i < parentElement.childNodes.length; ++i) {
        if (parentElement.childNodes[i].nodeName.toLowerCase() === 'input'
            && parentElement.childNodes[i].type === 'checkbox' && !parentElement.childNodes[i].checked)
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
    let day = daysFieldset.id.substring(0, 2)
    if (day === 'ne')
        day = 0
    else if (day === 'po')
        day = 1
    else if (day === 'ut')
        day = 2
    else if (day === 'st')
        day = 3
    else if (day === 'ct')
        day = 4
    else if (day === 'pa')
        day = 5
    else
        day = 6
    while (date.getDay() !== day)
        date.setDate(date.getDate() + 1)
}

function removeChildrenAfterLegend(element) {
    while (element.childNodes.length > 1 && element.lastChild.nodeName.toLowerCase() !== 'legend')
        element.removeChild(element.lastChild);

}

function getTrainingsPerWeekValue() {
    let val = document.getElementById('trainings_per_week').value
    if (val === 'one')
        val = 1
    else if (val === 'two')
        val = 2
    else
        val = 3
    return val
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
        const idToUncheck = rDays.find(d => document.getElementById(d).checked)
        document.getElementById(idToUncheck).click()
        --chosenCount
    }
    checkTrainingDaysOfTheWeekChosen()
}

function countChosenDays() {
    return days.filter(d => document.getElementById(d).checked).length
}

function displayTimeSettingForDay(element) {
    const newdisplay = element.checked ? 'block' : 'none'
    const daytimeid = `${element.id}_time`
    const daytime = document.getElementById(daytimeid)
    daytime.style.display = newdisplay
    setStateFromToFields(element.id, !element.checked)
}

function setStateFromToFields(id, state) {
    const f1id = `from_${id}`
    const f2id = `to_${id}`
    document.getElementById(f1id).disabled = state
    document.getElementById(f2id).disabled = state
}

function setStateAllDays(state) {
    days.filter(d => !document.getElementById(d).checked)
        .forEach(d => document.getElementById(d).disabled = !state)
}

function validateForm() {
    const trainingsPerWeek = getTrainingsPerWeekValue()
    const daysInWeekFieldset = document.getElementById('days_in_week')
    const firstUnchecked = getFirstUncheckedCheckboxIn(daysInWeekFieldset)
    const selectedDaysPerWeek = countCheckedCheckboxesIn(daysInWeekFieldset)
    if (trainingsPerWeek !== selectedDaysPerWeek) {
        firstUnchecked.setCustomValidity('Není vybrán odpovídající počet dní v týdnu vzhledem k počtu tréninků')
        return false
    } else {
        clearCustomValidityFromAllCheckboxesIn(daysInWeekFieldset)
        return true
    }
}

window.onload = function () {
    validateDate()
    const checkedIds = days.filter(d => document.getElementById(d).checked)
    checkedIds.forEach(id => dayToggled(document.getElementById(id)))
}