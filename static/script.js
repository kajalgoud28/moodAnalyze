async function login() {
    let email = document.getElementById("login-email").value;
    let password = document.getElementById("login-password").value;

    let response = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email, password: password })
    });

    let result = await response.json();
    alert(result.status === "success" ? "Login successful!" : "Invalid credentials!");
}

async function register() {
    let email = document.getElementById("reg-email").value;
    let password = document.getElementById("reg-password").value;

    let response = await fetch("/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email, password: password })
    });

    let result = await response.json();
    alert(result.status === "success" ? "Registration successful!" : "Email already registered!");
}

function captureSelfie() {
    let video = document.getElementById("video");
    let canvas = document.getElementById("canvas");
    let context = canvas.getContext("2d");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    let imageData = canvas.toDataURL("image/png");

    analyzeMood(imageData);
}

async function analyzeMood(image) {
    let response = await fetch("/analyze_mood", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image: image })
    });

    let result = await response.json();
    document.getElementById("mood-result").innerText = "Detected Mood: " + result.mood;
}

navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        document.getElementById("video").srcObject = stream;
    });
