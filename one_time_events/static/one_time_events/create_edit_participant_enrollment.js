window.addEventListener('load', event => {
    stateChanged()
})

function stateChanged() {
    const newValue = getStateElement().value
    let enableParticipantFee = false
    if(newValue === 'schvalen')
        enableParticipantFee = true


    getParticipationFeeDiv().style.display = enableParticipantFee ? 'block' : 'none'
    const participationFeeElement = getParticipationFeeElement()
    participationFeeElement.required = enableParticipantFee
    participationFeeElement.disabled = !enableParticipantFee
}

function getParticipationFeeDiv() {
    return document.getElementById('div_id_agreed_participation_fee')
}

function getParticipationFeeElement() {
    return document.getElementById('id_agreed_participation_fee')
}
