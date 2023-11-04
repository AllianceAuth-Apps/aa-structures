/* Global JS functions and symbols for Member Audit */

function setCookie(cname, cvalue, exhours) {
    const d = new Date();
    d.setTime(d.getTime() + (exhours * 60 * 60 * 1000));
    let expires = "expires=" + d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function getCookie(cname) {
    const name = cname + "=";
    const decodedCookie = decodeURIComponent(document.cookie);
    const ca = decodedCookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}


// sum numbers in column and write result in footer row
// Args:
// - api: current api object
// - columnIdx: Index number of columns to sum, starts with 0
// - format: format of output. either 'number' or 'isk'
function dataTableFooterSumColumn(api, columnIdx) {
    // Remove the formatting to get integer data for summation
    const intVal = function (i) {
        return typeof i === 'string' ?
            i.replace(/[\$,]/g, '') * 1 :
            typeof i === 'number' ?
                i : 0;
    };

    const columnTotal = api
        .column(columnIdx)
        .data()
        .reduce(function (a, b) {
            return intVal(a) + intVal(b);
        },
            0
        );
    $(api.column(columnIdx).footer()).html(
        columnTotal.toLocaleString('en-US', { maximumFractionDigits: 0 })
    );
}
