let occurrenciesIds = []

function loadOccurrences() {
    occurrenciesIds = [... document.getElementsByTagName('input')].filter(x=>x.type === 'checkbox').map(x=>x.id.split('-')[1])
}

window.addEventListener('load', event => {
    loadOccurrences()
    const position = $('#id_position_assignment')
    position.on('change', positionChanged)
    update(position.val())
})


function update(positionId) {
    if(positionId === undefined || positionId === '') {
        $('#occurrences-card').hide()
        return
    }
    else
        $('#occurrences-card').show()

    const max = $(`#position-${positionId}-capacity`).val()
    for (const oid of occurrenciesIds) {
        const actual = $(`#position-${positionId}-${oid}-count`).val()
        $(`#occurrence-${oid}-capacity`).text(max)
        $(`#occurrence-${oid}-count`).text(actual)
        const card = $(`#occurrence-${oid}-card`)
        const checkbox = $(`#occurrence-${oid}`)
        const checkboxIsDisabled = checkbox.prop('disabled')
        if(checkboxIsDisabled) {
            checkbox.prop('checked', false)
            showNotOpenedNotification()
        }
        if(actual >= max) {
            showCapacityNotification()
            card.addClass('bg-warning')
            if(!checkboxIsDisabled)
                notifyCheckboxDisable(checkbox)
        }
        else {
            card.removeClass('bg-warning')
            if(!checkboxIsDisabled)
                notifyCheckboxEnable(checkbox)
        }
    }
}

function showCapacityNotification() {
    $('#capacity-notification').show()
}

function showNotOpenedNotification() {
    $('#not-opened-notification').show()
}

function positionChanged() {
    const positionId = $('#id_position_assignment').val()
    update(positionId)
}