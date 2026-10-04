const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

const verifyForm = document.getElementById("verify-form");
const verifyMessage = document.getElementById("verify-message");

const savedEmail =
    localStorage.getItem("verification_email");


if (savedEmail) {

    document.getElementById("email").value =
        savedEmail;

}


verifyForm.addEventListener("submit", async (event) => {

    event.preventDefault();


    const email =
        document.getElementById("email").value.trim();

    const otp =
        document.getElementById("otp").value.trim();


    if (!/^\d{6}$/.test(otp)) {

        verifyMessage.textContent =
            "Please enter a valid 6-digit code.";

        return;
    }


    verifyMessage.textContent =
        "Verifying your email...";


    try {

        const response = await fetch(
            `${API_BASE_URL}/auth/verify-email`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    email: email,
                    otp: otp
                })
            }
        );


        const data = await response.json();


        if (!response.ok) {

            verifyMessage.textContent =
                data.detail || "Verification failed.";

            return;
        }


        localStorage.removeItem(
            "verification_email"
        );


        verifyMessage.textContent =
            "Email verified successfully. Redirecting to login...";


        setTimeout(() => {

            window.location.href = "/";

        }, 1000);


    } catch (error) {

        console.error(error);

        verifyMessage.textContent =
            "Unable to connect to ResearchMate.";
    }

});