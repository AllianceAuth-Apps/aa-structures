/* Logic for structure list page */

"use strict";

$(document).ready(function () {
    const COOKIE_LAST_TAB_ID = "structures_last_tab_id";
    const COOKIE_LAST_TAB_HOURS = 6;

    const dataExport = JSON.parse(
        document.getElementById("export-data").textContent
    );
    const filterTitles = dataExport.filter_titles;

    /* show last selected tab or default */
    let tabId = "";
    if (tabId != "") {
        setCookie(COOKIE_LAST_TAB_ID, tabId, 1);
    } else {
        tabId = getCookie(COOKIE_LAST_TAB_ID);
        if (tabId == "") tabId = "structures";
    }
    $('a[href="#' + tabId + '"]').tab("show");

    /* remember last selected tab */
    $('a[data-toggle="tab"]').on("shown.bs.tab", function (e) {
        const selectedTabId = $(e.target).attr("href").substr(1);
        setCookie(COOKIE_LAST_TAB_ID, selectedTabId, COOKIE_LAST_TAB_HOURS);
    });

    /* Datatable common definitions */
    const lengthMenu = [
        [10, 25, 50, 100, -1],
        [10, 25, 50, 100, "All"],
    ];
    const columnDefsVisible = [7, 8, 9, 10, 11, 12, 13, 14, 15];
    const defaultDef = {
        columns: [
            {
                data: "owner",
                render: {
                    _: "display",
                    sort: "value",
                },
            },
            {
                data: "location",
                render: {
                    _: "display",
                    sort: "value",
                },
            },
            {
                data: "type",
                render: {
                    _: "display",
                    sort: "value",
                },
            },
            { data: "structure_name_and_tags" },
            {
                data: "fuel_and_power",
                render: {
                    _: "display",
                    sort: "fuel_expires_at",
                },
            },
            { data: "state_details" },
            { data: "details" },

            /* hidden */
            { data: "alliance_name" },
            { data: "corporation_name" },
            { data: "region_name" },
            { data: "solar_system_name" },
            { data: "group_name" },
            { data: "is_reinforced_str" },
            { data: "state_str" },
            { data: "power_mode_str" },
            { data: "core_status_str" },
        ],
        lengthMenu: lengthMenu,
        paging: dataExport.data_tables_paging,
        pageLength: dataExport.data_tables_page_length,
        createdRow: function (row, data, dataIndex) {
            if (data["is_reinforced"]) {
                $(row).addClass("danger");
            }
        },
    };
    const structures_idx_start = 7;

    /* structures */
    $("#tab_structures").DataTable({
        ...defaultDef,
        ...{
            ajax: {
                url: dataExport.structures_ajax_url,
                dataSrc: "data",
                cache: false,
            },
            columnDefs: [
                { sortable: false, targets: [5, 6] },
                { visible: false, targets: columnDefsVisible },
            ],
            order: [
                [1, "asc"],
                [3, "asc"],
            ],
            filterDropDown: {
                columns: [
                    {
                        idx: structures_idx_start,
                        title: filterTitles.alliance,
                        maxWidth: "8em",
                    },
                    {
                        idx: structures_idx_start + 1,
                        title: filterTitles.corporation,
                        maxWidth: "9em",
                    },
                    {
                        idx: structures_idx_start + 2,
                        title: filterTitles.region,
                        maxWidth: "7em",
                    },
                    {
                        idx: structures_idx_start + 3,
                        title: filterTitles.solar_system,
                        maxWidth: "14em",
                    },
                    {
                        idx: structures_idx_start + 4,
                        title: filterTitles.group,
                        maxWidth: "7em",
                    },
                    {
                        idx: structures_idx_start + 5,
                        title: filterTitles.reinforced,
                    },
                    {
                        idx: structures_idx_start + 6,
                        title: filterTitles.state,
                        maxWidth: "6em",
                    },
                    {
                        idx: structures_idx_start + 7,
                        title: filterTitles.power_mode,
                        maxWidth: "12em",
                    },
                    {
                        idx: structures_idx_start + 8,
                        title: filterTitles.core,
                        maxWidth: "6em",
                    },
                ],
                autoSize: false,
                bootstrap: true,
            },
        },
    });

    $("#modalUpwellDetails").on("show.bs.modal", function (event) {
        $(this).find(".modal-title").html("Loading...");
        $(this)
            .find(".modal-body")
            .html(
                `<img class="center-image" src="${dataExport.spinner_image_url}">`
            );

        const button = $(event.relatedTarget);
        const ajax_url = button.data("ajax_url");
        $("#modalUpwellDetailsContent").load(
            ajax_url,
            null,
            (response, status, xhr) => {
                if (status != "success") {
                    $(this).find(".modal-title").html("Error");
                    $(this)
                        .find(".modal-body")
                        .html(
                            `<p class="text-danger">${xhr.status} ${xhr.statusText}</p>`
                        );
                }
            }
        );
    });

    /* pocos */
    const pocosColumnDefsVisible = [4, 5, ...columnDefsVisible];
    $("#tab_pocos").DataTable({
        ...defaultDef,
        ...{
            ajax: {
                url: dataExport.pocos_ajax_url,
                dataSrc: "data",
                cache: false,
            },
            columnDefs: [
                { sortable: false, targets: [5, 6] },
                { visible: false, targets: pocosColumnDefsVisible },
            ],
            order: [
                [1, "asc"],
                [3, "asc"],
            ],
            filterDropDown: {
                columns: [
                    {
                        idx: structures_idx_start,
                        title: filterTitles.alliance,
                        maxWidth: "8em",
                    },
                    {
                        idx: structures_idx_start + 1,
                        title: filterTitles.corporation,
                        maxWidth: "9em",
                    },
                    {
                        idx: structures_idx_start + 2,
                        title: filterTitles.region,
                        maxWidth: "7em",
                    },
                    {
                        idx: structures_idx_start + 3,
                        title: filterTitles.solar_system,
                        maxWidth: "14em",
                    },
                    {
                        idx: structures_idx_start + 4,
                        title: filterTitles.group,
                        maxWidth: "7em",
                    },
                    {
                        idx: structures_idx_start + 5,
                        title: filterTitles.reinforced,
                    },
                    {
                        idx: structures_idx_start + 6,
                        title: filterTitles.state,
                        maxWidth: "6em",
                    },
                ],
                autoSize: false,
                bootstrap: true,
            },
        },
    });

    $("#modalPocoDetails").on("show.bs.modal", function (event) {
        $(this).find(".modal-title").html("Loading...");
        $(this)
            .find(".modal-body")
            .html(
                `<img class="center-image" src="${dataExport.spinner_image_url}">`
            );

        const button = $(event.relatedTarget);
        const ajax_url = button.data("ajax_url");
        $("#modalPocoDetailsContent").load(
            ajax_url,
            null,
            (response, status, xhr) => {
                if (status != "success") {
                    $(this).find(".modal-title").html("Error");
                    $(this)
                        .find(".modal-body")
                        .html(
                            `<p class="text-danger">${xhr.status} ${xhr.statusText}</p>`
                        );
                }
            }
        );
    });

    /* starbases */
    $("#tab_starbases").DataTable({
        ...defaultDef,
        ...{
            ajax: {
                url: dataExport.starbases_ajax_url,
                dataSrc: "data",
                cache: false,
            },
            columnDefs: [
                { sortable: false, targets: [5, 6] },
                { visible: false, targets: columnDefsVisible },
            ],
            order: [
                [1, "asc"],
                [3, "asc"],
            ],
            filterDropDown: {
                columns: [
                    {
                        idx: structures_idx_start,
                        title: filterTitles.alliance,
                        maxWidth: "8em",
                    },
                    {
                        idx: structures_idx_start + 1,
                        title: filterTitles.corporation,
                        maxWidth: "9em",
                    },
                    {
                        idx: structures_idx_start + 2,
                        title: filterTitles.region,
                        maxWidth: "7em",
                    },
                    {
                        idx: structures_idx_start + 3,
                        title: filterTitles.solar_system,
                        maxWidth: "14em",
                    },
                    {
                        idx: structures_idx_start + 4,
                        title: filterTitles.group,
                        maxWidth: "7em",
                    },
                    {
                        idx: structures_idx_start + 5,
                        title: filterTitles.reinforced,
                    },
                    {
                        idx: structures_idx_start + 6,
                        title: filterTitles.state,
                        maxWidth: "6em",
                    },
                ],
                autoSize: false,
                bootstrap: true,
            },
        },
    });

    $("#modalStarbaseDetail").on("show.bs.modal", function (event) {
        $(this).find(".modal-title").html("Loading...");
        $(this)
            .find(".modal-body")
            .html(
                `<img class="center-image" src="${dataExport.spinner_image_url}">`
            );

        const button = $(event.relatedTarget);
        const ajax_url = button.data("ajax_url");
        $("#modalStarbaseDetailContent").load(
            ajax_url,
            null,
            (response, status, xhr) => {
                if (status != "success") {
                    $(this).find(".modal-title").html("Error");
                    $(this)
                        .find(".modal-body")
                        .html(
                            `<p class="text-danger">${xhr.status} ${xhr.statusText}</p>`
                        );
                }
            }
        );
    });

    /* jump gates */
    const jump_gate_idx_start = 7;
    $("#tab_jump_gates").DataTable({
        ajax: {
            url: dataExport.jump_gates_ajax_url,
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
                data: "location",
                render: {
                    _: "display",
                    sort: "value",
                },
            },
            {
                data: "type",
                render: {
                    _: "display",
                    sort: "value",
                },
            },
            { data: "structure_name_and_tags" },
            {
                data: "fuel_and_power",
                render: {
                    _: "display",
                    sort: "fuel_expires_at",
                },
            },
            {
                data: "jump_fuel_quantity",
                render: $.fn.dataTable.render.number(",", ".", 0),
            },
            { data: "state_details" },
            /* hidden */
            { data: "alliance_name" },
            { data: "corporation_name" },
            { data: "region_name" },
            { data: "solar_system_name" },
            { data: "is_reinforced_str" },
            { data: "power_mode_str" },
            { data: "state_str" },
        ],
        lengthMenu: lengthMenu,
        paging: dataExport.data_tables_paging,
        pageLength: dataExport.data_tables_page_length,
        order: [[1, "asc"]],
        columnDefs: [{ visible: false, targets: [7, 8, 9, 10, 11, 12, 13] }],
        filterDropDown: {
            columns: [
                {
                    idx: structures_idx_start,
                    title: filterTitles.alliance,
                    maxWidth: "8em",
                },
                {
                    idx: structures_idx_start + 1,
                    title: filterTitles.corporation,
                    maxWidth: "9em",
                },
                {
                    idx: structures_idx_start + 2,
                    title: filterTitles.region,
                    maxWidth: "7em",
                },
                {
                    idx: structures_idx_start + 3,
                    title: filterTitles.solar_system,
                    maxWidth: "14em",
                },
                {
                    idx: jump_gate_idx_start + 4,
                    title: filterTitles.reinforced,
                    maxWidth: "13em",
                },
                {
                    idx: jump_gate_idx_start + 5,
                    title: filterTitles.power_mode,
                    maxWidth: "12em",
                },
                {
                    idx: jump_gate_idx_start + 6,
                    title: filterTitles.state,
                    maxWidth: "6em",
                },
            ],
            autoSize: false,
            bootstrap: true,
        },
        createdRow: function (row, data, dataIndex) {
            if (data["is_reinforced"]) {
                $(row).addClass("danger");
            }
        },
    });
});
