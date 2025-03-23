document.addEventListener("DOMContentLoaded", function () {
    const wrapper = document.querySelector(".wrapper");
    const containerS = document.querySelector(".container-s");
    const containerL = document.querySelector(".container-l");
    const signupBtn = document.getElementById("signupBtn");
    const loginBtn = document.getElementById("loginBtn");

    function handleTransition(toSignup) {
        // Prevent multiple clicks during transition
        signupBtn.disabled = true;
        loginBtn.disabled = true;

        // Add transitioning class for green effect and text hiding
        containerS.classList.add("transitioning");
        containerL.classList.add("transitioning");

        // Toggle active class after text is hidden
        setTimeout(() => {
            if (toSignup) {
                wrapper.classList.add("active");
            } else {
                wrapper.classList.remove("active");
            }
        }, 100); // Faster toggle for smoother transition

        // Remove transitioning class after full transition
        setTimeout(() => {
            containerS.classList.remove("transitioning");
            containerL.classList.remove("transitioning");
            signupBtn.disabled = false;
            loginBtn.disabled = false;
        }, 400); // Slightly faster full transition
    }

    signupBtn.addEventListener("click", () => handleTransition(true));
    loginBtn.addEventListener("click", () => handleTransition(false));
});
