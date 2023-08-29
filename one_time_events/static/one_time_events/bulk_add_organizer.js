let occurrencies_ids = []

function loadOccurrences() {
    occurrencies_ids = [... document.getElementsByTagName('input')].filter(x=>x.type === 'checkbox').map(x=>x.id.split('-')[1])
}

window.addEventListener('load', event => {
    loadOccurrences()
    const position = $('#id_position_assignment')
    position.on('change', positionChanged)
    update(position.val())
})


function update(position_id) {
    if(position_id === undefined || position_id === '') {
        $('#occurrences-card').hide()
        return
    }
    else
        $('#occurrences-card').show()

    const max = $(`#position-${position_id}-capacity`).val()
    for (const oid of occurrencies_ids) {
        const actual = $(`#position-${position_id}-${oid}-count`).val()
        $(`#occurrence-${oid}-capacity`).text(max)
        $(`#occurrence-${oid}-count`).text(actual)
        let setCheckboxDisabled
        const card = $(`#occurrence-${oid}-card`)
        if(actual >= max) {
            card.addClass('bg-warning')
            setCheckboxDisabled = true
        }
        else {
            card.removeClass('bg-warning')
            setCheckboxDisabled = false
        }
        const checkbox = $(`#occurrence-${oid}`)
        checkbox.prop('disabled', setCheckboxDisabled)

        if((checkbox.prop('checked') && setCheckboxDisabled) || (!checkbox.prop('checked') && !setCheckboxDisabled))
            checkbox.prop('checked', !checkbox.prop('checked'))
    }
}

function positionChanged() {
    const position_id = $('#id_position_assignment').val()
    update(position_id)
}