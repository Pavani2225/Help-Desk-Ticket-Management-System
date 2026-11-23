
document.addEventListener("DOMContentLoaded", function () {

    // Mobile sidebar toggle
    const menuToggle = document.getElementById("sidebarToggle");
    const sidebar = document.getElementById("sidebar");

    if (menuToggle && sidebar) {

        menuToggle.addEventListener("click", function () {
            sidebar.classList.toggle("open");
        });

        // Close sidebar when clicking outside
        document.addEventListener("click", function (event) {

            if (
                window.innerWidth <= 768 &&
                sidebar.classList.contains("open") &&
                !sidebar.contains(event.target) &&
                !menuToggle.contains(event.target)
            ) {
                sidebar.classList.remove("open");
            }

        });
    }

    // Automatically hide flash messages
    const flashMessages = document.querySelectorAll(".flash");

    flashMessages.forEach(function (message) {

        setTimeout(function () {

            message.style.opacity = "0";
            message.style.transition = "opacity 0.4s ease";

            setTimeout(function () {
                message.remove();
            }, 400);

        }, 4000);

    });

    // Confirm logout
    const logoutForm = document.querySelector(
        '.sidebar-bottom form'
    );

    if (logoutForm) {

        logoutForm.addEventListener("submit", function (event) {

            const confirmed = confirm(
                "Are you sure you want to logout?"
            );

            if (!confirmed) {
                event.preventDefault();
            }

        });

    }

    // Highlight active sidebar navigation
    const currentPath = window.location.pathname;

    document.querySelectorAll(".sidebar-link").forEach(function (link) {

        const linkPath = new URL(link.href).pathname;

        if (linkPath === currentPath) {
            link.classList.add("active");
        }

    });

});
