function handler(event) {
    event.preventDefault();

    const form = event.target;

    const first_name = document.getElementById("id_first_name").value;
    const last_name = document.getElementById("id_last_name").value;

    const query_parameters = new URLSearchParams({
        first_name: first_name,
        last_name: last_name,
    });

    fetch("/api/osoby/existuje/?" + query_parameters.toString())
        .then((does_exist) => does_exist.json())
        .then((does_exist) => {
            if (does_exist === true) {
                const confirmed = window.confirm(
                    "Osoba s jménem " +
                    first_name +
                    " " +
                    last_name +
                    " již existuje. Chcete ji přesto přidat?"
                );

                if (!confirmed) return;
            }

            form.submit();
        });
}

document.getElementById("create-form").addEventListener("submit", handler);
