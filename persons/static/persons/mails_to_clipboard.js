const personsTableId = "persons-table";
const mailtoRegex = /mailto:([^"]+)/;

document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("copy-mails-to-clipboard").addEventListener("click", copyEmailsToClipboard);
});

function getEmailFromRow(row) {
    const match = row[1].match(mailtoRegex);
    return match ? match[1] : null;
}

function copyEmailsToClipboard() {
    if (!window.initializedDataTables || !window.initializedDataTables[personsTableId]) {
        return
    }

    let dataTable = window.initializedDataTables[personsTableId];
    let emails = dataTable.rows().data().map(getEmailFromRow).filter(e => e != null).join(", ");

    navigator.clipboard.writeText(emails);

    $(document).Toasts('create', {
        title: 'Notifikace',
        body: 'E-maily byly zkopírovány do schránky.',
        class: 'bg-success'
    })
}