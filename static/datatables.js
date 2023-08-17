$.extend($.fn.dataTable.defaults, {
    language: {
        url: '//cdn.datatables.net/plug-ins/1.13.4/i18n/cs.json',
    }
});

function datatableEnable(id, searchableColumns, orderableColumns, order = []) {
    $(function () {
        $("#" + id).DataTable({
            "columnDefs": [
                {"targets": searchableColumns, "searchable": true},
                {"targets": orderableColumns, "orderable": true},
                {"targets": "_all", "searchable": false, "orderable": false},
            ],
            "order": order,
        });
    });
}

function simpleOrderableTableEnable(id, orderableColumns, order = []) {
    $(function () {
        $("#" + id).DataTable({
            "columnDefs": [
                {"targets": orderableColumns, "orderable": true},
                {"targets": "_all", "searchable": false, "orderable": false},
            ],
            "order": order,
            "searching": false,
            "paging": false,
            "info":false
        });
    });
}