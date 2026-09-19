document.getElementById("firstLoginForm").addEventListener("submit", async function(event) {

    event.preventDefault();

    const email = document.getElementById("email").value;
    const otp = document.getElementById("otp").value;
    const newPassword = document.getElementById("newPassword").value;

    const response = await fetch("/first-login", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            email: email,
            otp: otp,
            new_password: newPassword
        })

    });

    const result = await response.json();

    document.getElementById("message").innerText =
        result.message;

    if (result.success) {

        setTimeout(() => {
            window.location.href = "/login";
        }, 1500);

    }

});