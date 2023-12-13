document.addEventListener("DOMContentLoaded", function () {
    const signupForm = document.getElementById("signup-form");
    const successPopup = document.getElementById("success-popup");
    const closePopupButton = document.getElementById("close-popup");

    signupForm.addEventListener("submit", async function (e) {
        e.preventDefault();

        const firstName = document.getElementById("first-name").value;
        const lastName = document.getElementById("last-name").value;
        const email = document.getElementById("email").value;

        // You can add client-side validation here

        // Send the signup data to the server using fetch or any other method
        const response = await fetch("/api/signup", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ FirstName: firstName, LastName: lastName, Email: email }),
        });

        if (response.ok) {
            // Show success popup
            successPopup.style.display = "block";
        }
    });

    closePopupButton.addEventListener("click", function () {
        // Close the success popup
        successPopup.style.display = "none";
    });
});
