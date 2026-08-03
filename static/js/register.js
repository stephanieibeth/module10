const registerForm = document.getElementById("register-form");
const messageElement = document.getElementById("message");
const registerButton = document.getElementById("register-button");

function showMessage(message, type) {
    messageElement.textContent = message;
    messageElement.className = `message ${type}`;
}

function validatePassword(password) {
    if (password.length < 6) {
        return "Password must be at least 6 characters long.";
    }

    if (!/[A-Z]/.test(password)) {
        return "Password must contain at least one uppercase letter.";
    }

    if (!/[a-z]/.test(password)) {
        return "Password must contain at least one lowercase letter.";
    }

    if (!/[0-9]/.test(password)) {
        return "Password must contain at least one number.";
    }

    return null;
}

function getErrorMessage(data) {
    if (typeof data.detail === "string") {
        return data.detail;
    }

    if (Array.isArray(data.detail)) {
        return data.detail
            .map((error) => error.msg)
            .join(" ");
    }

    if (data.error) {
        return String(data.error);
    }

    return "Registration failed. Please check your information.";
}

registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    showMessage("", "");

    const firstName = document.getElementById("first-name").value.trim();
    const lastName = document.getElementById("last-name").value.trim();
    const username = document.getElementById("username").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const confirmPassword =
        document.getElementById("confirm-password").value;

    if (!firstName || !lastName || !username || !email || !password) {
        showMessage("Please complete all required fields.", "error");
        return;
    }

    if (username.length < 3) {
        showMessage(
            "Username must be at least 3 characters long.",
            "error"
        );
        return;
    }

    const passwordError = validatePassword(password);

    if (passwordError) {
        showMessage(passwordError, "error");
        return;
    }

    if (password !== confirmPassword) {
        showMessage("Passwords do not match.", "error");
        return;
    }

    const registrationData = {
        first_name: firstName,
        last_name: lastName,
        email: email,
        username: username,
        password: password
    };

    registerButton.disabled = true;
    registerButton.textContent = "Registering...";

    try {
        const response = await fetch("/users/register", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(registrationData)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(getErrorMessage(data));
        }

        showMessage(
            "Registration successful! You can now log in.",
            "success"
        );

        registerForm.reset();
    } catch (error) {
        showMessage(error.message, "error");
    } finally {
        registerButton.disabled = false;
        registerButton.textContent = "Register";
    }
});
