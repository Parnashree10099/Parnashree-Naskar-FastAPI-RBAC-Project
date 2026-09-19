document.getElementById("registerForm").addEventListener("submit", async function(event) {

    event.preventDefault();

    const fullName = document.getElementById("fullName").value;
    const email = document.getElementById("email").value;
    const phone = document.getElementById("phone").value;
    const dob = document.getElementById("dob").value;
    const password = document.getElementById("password").value;

    const role = document.getElementById("role").value;
    const subject = document.getElementById("subject").value;
    const standard = document.getElementById("standard").value;

    const response = await fetch("/register", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({

            full_name: fullName,
            email: email,
            phone: phone,
            dob: dob,
            password: password,

            role: role,
            subject: subject,
            standard: standard

        })
    });

    const result = await response.json();

    console.log("BACKEND RESULT:", result);

    document.getElementById("message").innerText = result.message;

    if (response.ok) {

        setTimeout(() => {
            window.location.assign("/verify");
        }, 1000);

    }

});
