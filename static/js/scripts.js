document.addEventListener("DOMContentLoaded", function () {
    const categoryLinks = document.querySelectorAll(".categories-search .btn-primary");

    categoryLinks.forEach((link) => {
        link.addEventListener("click", function (event) {
            event.preventDefault(); // block redirect

            const parent = link.parentElement;

            // If subcategories exist - switch on visibility
            let subcategories = parent.querySelector(".subcategories");
            if (subcategories) {
                parent.classList.toggle("active");
            } else {
                // Dynamical load of subcategories
                subcategories = document.createElement("ul");
                subcategories.classList.add("subcategories");

                // Simulation of subcategories
                const dummySubcategories = ["Subkategorie 1", "Subkategorie 2", "Subkategorie 3"];
                dummySubcategories.forEach((name) => {
                    const subItem = document.createElement("li");
                    subItem.textContent = name; //subcategory name
                    subcategories.appendChild(subItem);
                });

                parent.appendChild(subcategories);
                parent.classList.add("active");
            }
        });
    });
});