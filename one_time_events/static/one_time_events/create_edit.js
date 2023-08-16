function dateChanged() {
    validateDate()
    updateOccurrences()
}

function dayCheckboxClicked(checkboxElm) {
    const display = checkboxElm.checked ? 'block' : 'none'
    const date = checkboxElm.id.split('_')[0]
    const hoursElm = document.getElementById(`${date}_hours`)
    hoursElm.required = checkboxElm.checked
    hoursElm.disabled = !checkboxElm.checked
    const containerElm = hoursElm.parentElement.parentElement
    containerElm.style.display = display
    setReportValidity(getFirstOccurrenceCheckbox(), '', true)

}

window.onbeforeunload = function () {
    localStorage.clear()
}

function beforeSubmit() {
    return validateForm()
}

function validateForm() {
    return validateDate(true) && validateAtLeastOneDayChecked(true)
}

function validateDate(report = false) {
    const timeStartDate = convertCzechDate(document.getElementById('id_date_start').value)
    const timeEndEl = document.getElementById('id_date_end')
    const timeEndDate = convertCzechDate(timeEndEl.value)
    const span = timeEndDate.getTime() - timeStartDate.getTime()
    if (span < 0 || isNaN(span)) {
        window._datesValid = false
        setReportValidity(timeEndEl, 'Konec události nesmí být dříve než její začátek', report)
        return false
    } else {
        window._datesValid = true
        setReportValidity(timeEndEl, '', report)
        return true
    }
}

function validateAtLeastOneDayChecked(report = false) {
    const firstCheckbox = getFirstOccurrenceCheckbox()
    if(countCheckedDays() === 0) {
        setReportValidity(firstCheckbox, 'Jednorázová událost se musí alespoň jedenkrát konat', report)
        return false
    }
    else {
        setReportValidity(firstCheckbox, '', report)
        return true
    }

}

function countCheckedDays() {
    let total = 0
    const inputs = getEventScheduleRowElement().getElementsByTagName('input')
    for(let i = 0; i < inputs.length; i += 2) {
        const checkbox = inputs[i]
        if(checkbox.checked)
            ++total
    }
    return total
}

function getFirstOccurrenceCheckbox() {
    return getEventScheduleRowElement().getElementsByTagName('input')[0]
}



function updateOccurrences() {
    saveDeleteOccurrences()
    if(window._datesValid)
        createRestoreOccurrences()
}

function saveDeleteOccurrences() {
    const inputs = getEventScheduleRowElement().getElementsByTagName('input')
    for(let i = 0; i < inputs.length - 1; i+=2) {
        const checkboxElm = inputs[i]
        const hoursElm = inputs[i+1]
        const date = checkboxElm.id.split('_')[0]
        localStorage.setItem(`${date}_checkbox`, checkboxElm.checked)
        if(hoursElm.value !== "")
            localStorage.setItem(`${date}_hours`, hoursElm.value)
    }
    clearOccurrences()
}

function createRestoreOccurrences() {
    const dateStart = getDateStartParsed()
    const dateEnd = getDateEndParsed()
    while(dateStart <= dateEnd) {
        const czechDateFormatted = formatCzechDate(dateStart)
        let checkboxState = localStorage.getItem(`${czechDateFormatted}_checkbox`)
        if(checkboxState === null)
            checkboxState = 'true'

        let hours = localStorage.getItem(`${czechDateFormatted}_hours`)
        if(hours == null)
            hours = undefined

        const dayCardHtml = dayCard(czechDateFormatted, checkboxState, hours)
        $('#event-schedule-row').append(dayCardHtml)

        dateStart.setDate(dateStart.getDate() + 1)
    }
}

function getEventScheduleRowElement() {
    return document.getElementById('event-schedule-row')
}

function getDateParsed(id) {
    const dateRaw = document.getElementById(id).value
    return parseCzechDate(dateRaw)
}

function getDateStartParsed() {
    return getDateParsed('id_date_start')
}

function getDateEndParsed() {
    return getDateParsed('id_date_end')
}

function clearOccurrences() {
    getEventScheduleRowElement().innerText = ''
}

function dayCard(day, checked='true', hours=undefined) {
    let str = '<div class="col-sm-5 col-md-3 col-lg-3 col-12"> <div class="card"> <div class="card-header border-0"> <div class="card-title h5 text-bold"> <input id="{0}_checkbox" name="dates" type="checkbox" value="{0}" onclick="dayCheckboxClicked(this)" {1}> <label for="{0}_checkbox">{0}</label> </div></div><div class="card-body p-0"> <div class="row"> <div class="col-12 px-4"> <div class="form-group" {3}> <label for="{0}_hours">Počet hodin*</label> <div> <input id="{0}_hours" name="hours" class="form-control" min="1" max="10" type="number" {4} value="{2}"> </div></div></div></div></div></div></div>'
    str = str.replaceAll('{0}', day)
    if(checked === 'true') {
        str = str.replaceAll('{1}', 'checked')
        str = str.replaceAll('{3}', '')
        str = str.replaceAll('{4}', 'required')
    }
    else {
        str = str.replaceAll('{1}', '')
        str = str.replaceAll('{3}', 'style="display: none"')
        str = str.replaceAll('{4}', 'disabled')
    }
    if(hours !== undefined)
        str = str.replaceAll('{2}', hours)
    else
        str = str.replaceAll('{2}', '')

    return str
}