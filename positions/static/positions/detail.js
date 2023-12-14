function addQualificationClicked() {
    const modalElement = getModalTitleElement()
    modalElement.innerText = 'Přidat kvalifikaci'
    getQualificationBody().style.display = ''
    getPermissionsBody().style.display = 'none'
    getEquipmentBody().style.display = 'none'

}

function addPermissionClicked() {
    const modalElement = getModalTitleElement()
    modalElement.innerText = 'Přidat oprávnění'
    getQualificationBody().style.display = 'none'
    getPermissionsBody().style.display = ''
    getEquipmentBody().style.display = 'none'
}

function addEquipmentClicked() {
    const modalElement = getModalTitleElement()
    modalElement.innerText = 'Přidat vybavení'
    getQualificationBody().style.display = 'none'
    getPermissionsBody().style.display = 'none'
    getEquipmentBody().style.display = ''
}

function getModalTitleElement() {
    return document.getElementById('modal-title-feature')
}

function getQualificationBody() {
    return document.getElementById('qualifications-body')
}

function getPermissionsBody() {
    return document.getElementById('permissions-body')
}

function getEquipmentBody() {
    return document.getElementById('equipment-body')
}