/* Logic for statistics page */

"use strict";

$(document).ready(function () {
    const dataExport = JSON.parse(
        document.getElementById("export-data").textContent
    );
    const filterTitles = dataExport.filter_titles;

    /* summary */
    $("#tab_summary").DataTable({
        ajax: {
            url: dataExport.ajax_url,
            dataSrc: "data",
            cache: false,
        },
        columns: [
            {
                data: "owner",
                render: {
                    _: "display",
                    sort: "value",
                },
            },
            {
                data: "citadel_count",
                render: $.fn.dataTable.render.number(",", ".", 0),
            },
            {
                data: "ec_count",
                render: $.fn.dataTable.render.number(",", ".", 0),
            },
            {
                data: "refinery_count",
                render: $.fn.dataTable.render.number(",", ".", 0),
            },
            {
                data: "other_count",
                render: $.fn.dataTable.render.number(",", ".", 0),
            },
            {
                data: "poco_count",
                render: $.fn.dataTable.render.number(",", ".", 0),
            },
            {
                data: "starbase_count",
                render: $.fn.dataTable.render.number(",", ".", 0),
            },
            {
                data: "total",
                render: $.fn.dataTable.render.number(",", ".", 0),
            },
            /* hidden */
            { data: "alliance_name" },
        ],
        lengthMenu: [
            [10, 25, 50, 100, -1],
            [10, 25, 50, 100, "All"],
        ],
        paging: dataExport.data_tables_paging,
        pageLength: dataExport.data_tables_page_length,
        order: [[0, "asc"]],
        columnDefs: [{ visible: false, targets: [8] }],
        filterDropDown: {
            columns: [
                {
                    idx: 8,
                    title: filterTitles.alliance,
                    maxWidth: "11em",
                },
            ],
            autoSize: false,
            bootstrap: true,
        },
        footerCallback: function (row, data, start, end, display) {
            const api = this.api();
            const summary_total_idx_start = 1;

            dataTableFooterSumColumn(api, summary_total_idx_start);
            dataTableFooterSumColumn(api, summary_total_idx_start + 1);
            dataTableFooterSumColumn(api, summary_total_idx_start + 2);
            dataTableFooterSumColumn(api, summary_total_idx_start + 3);
            dataTableFooterSumColumn(api, summary_total_idx_start + 4);
            dataTableFooterSumColumn(api, summary_total_idx_start + 5);
            dataTableFooterSumColumn(api, summary_total_idx_start + 6);
        },
    });
});
