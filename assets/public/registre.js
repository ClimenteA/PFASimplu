let elemsToHide = [
    "barChart",
    "total-profit",
    "total-incasari",
    "total-cheltuieli",
    "tabel-incasari",
    "tabel-cheltuieli",
    "tabel-declaratii",
    "tabel-incasari-download",
    "tabel-cheltuieli-download"
];

let summary = document.getElementById("total-incasari");
let extraTables = document.getElementById("total-cheltuieli");

let showAllReports = true;
document.getElementById("display-reports").addEventListener("change", event => {
    showAllReports = !showAllReports
    if (!showAllReports) {
        elemsToHide.forEach(elId => {
            document.getElementById(elId).classList.add("none")
        })
    } else {
        elemsToHide.forEach(elId => {
            document.getElementById(elId).classList.remove("none")
        })
    };

}, false);


const queryString = window.location.search;
const urlParams = new URLSearchParams(queryString);
const anul = urlParams.get("anul");

let selectedYear = document.getElementById("selected-year")

if (anul) {
    document.getElementById(anul).setAttribute("selected", "")
}

selectedYear.addEventListener("click", event => {
    let url = String(document.location).split("?")[0] + selectedYear.value;
    const link = document.createElement('a');
    link.href = url;
    link.click();
}, false);


