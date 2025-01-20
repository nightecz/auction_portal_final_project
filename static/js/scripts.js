document.addEventListener("DOMContentLoaded", function () {
    const categoryLinks = document.querySelectorAll(".categories-search .btn-primary");

    categoryLinks.forEach((link) => {
        link.addEventListener("click", function (event) {
            event.preventDefault(); // Zabrání přesměrování

            const parent = link.parentElement;

            // Pokud již subkategorie existují, přepnout jejich viditelnost
            let subcategories = parent.querySelector(".subcategories");
            if (subcategories) {
                parent.classList.toggle("active");
            } else {
                // Dynamicky načíst subkategorie (simulováno zde)
                subcategories = document.createElement("ul");
                subcategories.classList.add("subcategories");

                // Simulace subkategorií, v reálu by se načetly přes Django nebo API
                const dummySubcategories = ["Subkategorie 1", "Subkategorie 2", "Subkategorie 3"];
                dummySubcategories.forEach((name) => {
                    const subItem = document.createElement("li");
                    subItem.textContent = name; // Název subkategorie
                    subcategories.appendChild(subItem);
                });

                parent.appendChild(subcategories);
                parent.classList.add("active");
            }
        });
    });
});
