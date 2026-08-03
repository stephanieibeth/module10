const loginForm = document.getElementById("login-form");
const messageElement = document.getElementById("message");
const loginButton = document.getElementById("login-button");

function showMessage(message, type) {
    messageElement.textContent = message;
    messageElement.className = `message ${type}`;
}

function getErrorMessage(data, statusCode) {
    if (typeof data.detail === "string") {
        return data.detail;
    }

    if (Array.isArray(data.detail)) {
        return data.detail
            .map((error) => {
                if (typeof error === "string") {
                    return error;
                }

                return error.msg || "Invalid login information.";
            })
            .join(" ");
    }

    if (typeof data.error === "string") {
        return data.error;
    }

    if (Array.isArray(data.error)) {
        return data.error.join(" ");
    }

    if (statusCode === 401) {
        return "Invalid username or password";
    }

    return "Login failed. Please check your credentials.";
}

loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    showMessage("", "");

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;

    if (!username || !password) {
        showMessage("Please enter your username and password.", "error");
        return;
    }

    loginButton.disabled = true;
    loginButton.textContent = "Logging in...";

    try {
        const response = await fetch("/users/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(getErrorMessage(data, response.status));
        }

        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("token_type", data.token_type);

        if (data.user) {
            localStorage.setItem("user", JSON.stringify(data.user));
        }

        showMessage("Login successful!", "success");
        loginForm.reset();
    } catch (error) {
        showMessage(error.message, "error");
    } finally {
        loginButton.disabled = false;
        loginButton.textContent = "Log In";
    }
});