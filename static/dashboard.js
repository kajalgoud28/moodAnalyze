document.addEventListener("DOMContentLoaded", function () {
    fetch("http://127.0.0.1:5000/dashboard-data")
    .then(response => response.json())
    .then(data => {
        console.log("Fetched Data:", data); // Debugging

        if (data.sleep_logs.length > 0) {
            renderSleepChart(data.sleep_logs);
        } else {
            console.warn("No sleep data available.");
        }

        if (data.mood_logs.length > 0) {
            renderMoodChart(data.mood_logs);
        } else {
            console.warn("No mood data available.");
        }
    })
    .catch(error => console.error("Error fetching data:", error));
});

function renderSleepChart(sleepData) {
    let ctx = document.getElementById("sleepChart").getContext("2d");
    let labels = sleepData.map(entry => entry.date || "Unknown");
    let values = sleepData.map(entry => entry.duration || 0);

    new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: "Sleep Duration (Hours)",
                data: values,
                borderColor: "blue",
                fill: false
            }]
        },
        options: {
            responsive: true
        }
    });
}

function renderMoodChart(moodData) {
    let ctx = document.getElementById("moodChart").getContext("2d");
    let labels = moodData.map(entry => entry.date || "Unknown");
    let values = moodData.map(entry => entry.mood_score || 0);

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Mood Score",
                data: values,
                backgroundColor: "green"
            }]
        },
        options: {
            responsive: true
        }
    });
}
