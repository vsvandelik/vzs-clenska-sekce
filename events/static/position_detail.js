const addFeatureTable = new DataTable('#addFeatureTable', {
    responsive: true,
    searching: true
})

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
    return document.getElementById('modalTitle')
}

function getQualificationBody() {
    return document.getElementById('qualificationsBody')
}

function getPermissionsBody() {
    return document.getElementById('permissionsBody')
}

function getEquipmentBody() {
    return document.getElementById('equipmentBody')
}