
document.addEventListener("DOMContentLoaded", function () {

    const dataElement = document.getElementById("dashboard-data");

    if (!dataElement) return;

    const dashboardData = JSON.parse(dataElement.textContent);

    // Priority Doughnut Chart
    const priorityCanvas = document.getElementById("priorityChart");

    if (priorityCanvas && typeof Chart !== "undefined") {
        new Chart(priorityCanvas, {
            type: "doughnut",
            data: {
                labels: dashboardData.priorityLabels,
                datasets: [{
                    data: dashboardData.priorityValues,
                    backgroundColor: [
                        "#ef4444",
                        "#f97316",
                        "#eab308",
                        "#22c55e"
                    ],
                    borderWidth: 0,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "68%",
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: {
                            color: "#aebbd0",
                            padding: 18,
                            usePointStyle: true
                        }
                    }
                }
            }
        });
    }

    // Ticket Status Bar Chart
    const statusCanvas = document.getElementById("statusChart");

    if (statusCanvas && typeof Chart !== "undefined") {
        new Chart(statusCanvas, {
            type: "bar",
            data: {
                labels: dashboardData.statusLabels,
                datasets: [{
                    label: "Tickets",
                    data: dashboardData.statusValues,
                    backgroundColor: [
                        "#6366f1",
                        "#38bdf8",
                        "#22c55e",
                        "#64748b"
                    ],
                    borderRadius: 7,
                    maxBarThickness: 48
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: "#aebbd0"
                        },
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: "#aebbd0",
                            precision: 0
                        },
                        grid: {
                            color: "rgba(148,163,184,0.12)"
                        }
                    }
                }
            }
        });
    }

    // Weekly Ticket Activity Line Chart
    const trendCanvas = document.getElementById("ticketTrendChart");

    if (trendCanvas && typeof Chart !== "undefined") {
        new Chart(trendCanvas, {
            type: "line",
            data: {
                labels: dashboardData.weeklyLabels,
                datasets: [
                    {
                        label: "Created",
                        data: dashboardData.weeklyCreated,
                        borderColor: "#818cf8",
                        backgroundColor: "rgba(129, 140, 248, 0.12)",
                        fill: true,
                        tension: 0.4,
                        pointRadius: 4,
                        pointHoverRadius: 7
                    },
                    {
                        label: "Resolved",
                        data: dashboardData.weeklyResolved,
                        borderColor: "#34d399",
                        backgroundColor: "rgba(52, 211, 153, 0.10)",
                        fill: true,
                        tension: 0.4,
                        pointRadius: 4,
                        pointHoverRadius: 7
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: "index"
                },
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: {
                            color: "#aebbd0",
                            usePointStyle: true,
                            padding: 20
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: "#aebbd0"
                        },
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: "#aebbd0",
                            precision: 0
                        },
                        grid: {
                            color: "rgba(148,163,184,0.12)"
                        }
                    }
                }
            }
        });
    }

    // SLA Progress Animation
    const slaFill = document.querySelector(".sla-fill");

    if (slaFill) {
        const width = Number(slaFill.dataset.width);

        slaFill.style.width =
            Math.max(0, Math.min(100, width)) + "%";
    }

    // Technician Performance Progress Bars
    const technicianBars = document.querySelectorAll(
        ".technician-progress-fill"
    );

    technicianBars.forEach(function (bar) {
        const percentage = Number(bar.dataset.width);

        if (Number.isFinite(percentage)) {
            bar.style.width =
                Math.max(0, Math.min(100, percentage)) + "%";
        }
    });

});
