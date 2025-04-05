/* Logic for public page */

"use strict";

$(document).ready(function () {
    /* Import data from template */
    const dataExport = JSON.parse(
        document.getElementById("export-data").textContent
    );
    const filterTitles = dataExport.filter_titles;

    /* pocos */
    let pocos_idx_start = 6;
    $("#tab_pocos").DataTable({
        ajax: {
            url: dataExport.ajax_url,
            dataSrc: "data",
            cache: false,
        },
        columns: [
            {
                data: "planet_plus_icon",
                render: {
                    _: "display",
                    sort: "sort",
                },
            },
            {
                data: "solar_system_html",
                render: {
                    _: "display",
                    sort: "sort",
                },
            },
            {
                data: "constellation_html",
                render: {
                    _: "display",
                    sort: "sort",
                },
            },
            {
                data: "owner",
                render: {
                    _: "display",
                    sort: "value",
                },
            },
            {
                data: "has_access_html",
                render: {
                    _: "display",
                    sort: "sort",
                },
            },
            {
                data: "tax",
                render: {
                    _: "display",
                    sort: "sort",
                },
            },

            /* hidden columns */
            { data: "constellation" },
            { data: "planet_type_name" },
            { data: "space_type" },
            { data: "region" },
            { data: "solar_system" },
            { data: "corporation_name" },
            { data: "alliance_name" },
            { data: "has_access_str" },
        ],
        lengthMenu: [
            [10, 25, 50, 100, -1],
            [10, 25, 50, 100, "All"],
        ],
        paging: dataExport.data_tables_paging,
        pageLength: dataExport.data_tables_page_length,
        columnDefs: [{ visible: false, targets: [6, 7, 8, 9, 10, 11, 12, 13] }],
        order: [
            [8, "asc"],
            [9, "asc"],
            [0, "asc"],
        ],
        rowGroup: {
            dataSrc: "constellation",
            className: "table-group",
        },
        filterDropDown: {
            columns: [
                {
                    idx: pocos_idx_start,
                    title: filterTitles.constellation,
                    maxWidth: "10em",
                },
                {
                    idx: pocos_idx_start + 1,
                    title: filterTitles.planet_type,
                    maxWidth: "10em",
                },
                {
                    idx: pocos_idx_start + 2,
                    title: filterTitles.space_type,
                    maxWidth: "10em",
                },
                {
                    idx: pocos_idx_start + 3,
                    title: filterTitles.region,
                    maxWidth: "10em",
                },
                {
                    idx: pocos_idx_start + 4,
                    title: filterTitles.solar_system,
                    maxWidth: "10em",
                },
                {
                    idx: pocos_idx_start + 5,
                    title: filterTitles.corporation,
                    maxWidth: "10em",
                },
                {
                    idx: pocos_idx_start + 6,
                    title: filterTitles.alliance,
                    maxWidth: "10em",
                },
                {
                    idx: pocos_idx_start + 7,
                    title: filterTitles.access,
                    maxWidth: "10em",
                },
            ],
            autoSize: false,
            bootstrap: true,
            bootstrap_version: 5,
        },
    });
});
