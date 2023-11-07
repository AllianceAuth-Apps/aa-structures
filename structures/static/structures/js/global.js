/* Global JS functions and symbols */

"use strict";

/**
 * Set a cookie.
 * @param {string} name Name of the cookie
 * @param {string} value Value of the cookie
 * @param {intVal} hours Lifetime of the cookie in hours
 */
function setCookie(name, value, hours) {
    const d = new Date();

    d.setTime(d.getTime() + hours * 60 * 60 * 1000);
    let expires = "expires=" + d.toUTCString();
    document.cookie = name + "=" + value + ";" + expires + ";path=/";
}

/**
 * Get value of a cookie.
 * @param {string} name Name of the cookie
 * @returns Value of the cookie or an empty string if the cookie was not found
 */
function getCookie(name) {
    const cname = name + "=";
    const decodedCookie = decodeURIComponent(document.cookie);
    const ca = decodedCookie.split(";");

    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) == " ") {
            c = c.substring(1);
        }
        if (c.indexOf(cname) == 0) {
            return c.substring(cname.length, c.length);
        }
    }

    return "";
}

/**
 * Sum numbers in column and write result in footer row.
 * @param {object} api Api object of the datatable
 * @param {intVal} columnIdx Index number of columns to sum, starts with 0
 */
function dataTableFooterSumColumn(api, columnIdx) {
    // Remove the formatting to get integer data for summation
    const intVal = function (i) {
        return typeof i === "string"
            ? i.replace(/[\$,]/g, "") * 1
            : typeof i === "number"
            ? i
            : 0;
    };

    const columnTotal = api
        .column(columnIdx)
        .data()
        .reduce(function (a, b) {
            return intVal(a) + intVal(b);
        }, 0);

    $(api.column(columnIdx).footer()).html(
        columnTotal.toLocaleString("en-US", { maximumFractionDigits: 0 })
    );
}
