const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

const loginForm = document.getElementById("login-form");
const loginMessage = document.getElementById("login-message");


loginForm.addEventListener("submit", async (event) => {

    event.preventDefault();


    const email =
        document.getElementById("email").value.trim();

    const password =
        document.getElementById("password").value;


    loginMessage.textContent =
        "Logging in...";


    try {

        const response = await fetch(
            `${API_BASE_URL}/auth/login`,
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

            loginMessage.textContent =
                data.detail || "Login failed.";

            return;
        }


        localStorage.setItem(
            "access_token",
            data.access_token
        );


        loginMessage.textContent =
            "Login successful!";


        setTimeout(() => {

            window.location.href =
                "/chat/";

        }, 300);


    } catch (error) {

        console.error(error);

        loginMessage.textContent =
            "Unable to connect to ResearchMate.";
    }

});