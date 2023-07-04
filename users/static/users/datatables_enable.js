function datatables_enable(id, searchable_columns, sorted_column = []) {
    $(document).ready(function () {
        $("#" + id).DataTable({
            "columnDefs": [
                { "targets": searchable_columns, "searchable": true },
                { "targets": "_all", "searchable": false },
            ],
            "order": [sorted_column],
        });
    });
}
