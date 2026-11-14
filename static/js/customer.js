function confirmOrder() {

    return confirm(
        "Are you sure you want to place this order?"
    );

}


function confirmDelete() {

    return confirm(
        "Are you sure you want to delete this item?"
    );

}


function updateQuantity(
    input,
    max
) {

    let value = parseInt(input.value);

    if (value < 1) {
        input.value = 1;
    }

    if (value > max) {
        input.value = max;
    }

}

function searchProducts() {

    let input =
        document.getElementById(
            "productSearch"
        );

    let filter =
        input.value.toLowerCase();

    let cards =
        document.querySelectorAll(
            ".product-card"
        );


    cards.forEach(function(card) {

        let text =
            card.textContent.toLowerCase();

        if (text.includes(filter)) {

            card.style.display = "";

        } else {

            card.style.display = "none";

        }

    });

}