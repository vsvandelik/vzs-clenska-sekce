$.extend($.fn.dataTable.defaults, {
    language: {
        url: '//cdn.datatables.net/plug-ins/1.13.4/i18n/cs.json',
    }
});

function datatables_enable(id, searchable_columns, orderable_columns, order = []) {
    $(document).ready(function () {
        $("#" + id).DataTable({
            "columnDefs": [
                {"targets": searchable_columns, "searchable": true},
                {"targets": orderable_columns, "orderable": true},
                {"targets": "_all", "searchable": false, "orderable": false},
            ],
            "order": order,
        });
    });
}
