const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

const registerForm = document.getElementById("register-form");
const registerMessage = document.getElementById("register-message");


registerForm.addEventListener("submit", async (event) => {

    event.preventDefault();

    const email =
        document.getElementById("email").value.trim();

    const password =
        document.getElementById("password").value;

    const confirmPassword =
        document.getElementById("confirm-password").value;


    if (password !== confirmPassword) {

        registerMessage.textContent =
            "Passwords do not match.";

        return;
    }


    registerMessage.textContent =
        "Creating your account...";


    try {

        const response = await fetch(
            `${API_BASE_URL}/auth/register`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    email: email,
                    password: password
                })
            }
        );


        const data = await response.json();


        if (!response.ok) {

            registerMessage.textContent =
                data.detail || "Registration failed.";

            return;
        }


        // Save email for the verification page.
        localStorage.setItem(
            "verification_email",
            data.email
        );


        registerMessage.textContent =
            "Account created. Check your email for the verification code.";


        setTimeout(() => {

            window.location.href =
                "/verify-email/";

        }, 800);


    } catch (error) {

        console.error(error);

        registerMessage.textContent =
            "Unable to connect to ResearchMate.";
    }

});