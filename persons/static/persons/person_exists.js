function handler(event) {
    event.preventDefault();

    const form = event.target;
    const elements = form.elements;

    const csrf_token = elements["csrfmiddlewaretoken"].value;
    const first_name = elements["first_name"].value;
    const last_name = elements["last_name"].value;

    const request = new Request("/api/persons/exists/", {
        method: "POST",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": csrf_token,
        },
        mode: "same-origin",
        body: JSON.stringify({
            first_name: first_name,
            last_name: last_name,
        }),
    });

    fetch(request)
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
