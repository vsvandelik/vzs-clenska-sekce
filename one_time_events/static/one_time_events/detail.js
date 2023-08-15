function signupPersonClicked() {
    getSignupPersonModalTitle().innerText = 'Přihlásit osobu'
    getSignupPersonForm().action = window._signPersonUrl
    setAddButtonsState('přihlášen')
}

function addSubstituteClicked() {
    getSignupPersonModalTitle().innerText = 'Přihlásit náhradníka'
    getSignupPersonForm().action = window._addSubstituteUrl
    setAddButtonsState('náhradník')
}

function getSignupPersonForm() {
    return document.getElementById('signup-person-form')
}

function getSignupPersonModalTitle() {
    return document.getElementById('signup-person-title')
}

window.onload = function() {
    window._signPersonUrl = getDjangoUrl('sign-url')
    window._addSubstituteUrl = getDjangoUrl('substitute-url')
}

function setAddButtonsState(disableTxt) {
    const lines = document.getElementById('signup-person-tbody').getElementsByTagName('tr')
    for (const line of lines)
        line.children[1].children[0].disabled = getBadgeText(line.children[0]) === disableTxt;

}

function getBadgeText(td) {
    if(td.children.length === 2)
        return td.children[1].innerText
    return ''
}