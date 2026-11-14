function confirmAction(message) {

    return confirm(message);

}


function searchTable() {

    let input =
        document.getElementById(
            "searchInput"
        );

    let filter =
        input.value.toLowerCase();

    let table =
        document.getElementById(
            "dataTable"
        );

    let rows =
        table.getElementsByTagName("tr");


    for (
        let i = 1;
        i < rows.length;
        i++
    ) {

        let text =
            rows[i].textContent
                .toLowerCase();

        if (text.includes(filter)) {

            rows[i].style.display = "";

        } else {

            rows[i].style.display = "none";

        }

    }

}