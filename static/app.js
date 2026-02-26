const targets = document.querySelectorAll(".target");
const nextBtn = document.getElementById("next-btn");
const dialog = document.getElementById("result-dialog");
const dialogText = document.getElementById("dialog-text");

targets.forEach(target => {
  target.addEventListener("click", function (e) {
    // Prevent multiple clicks if dialog is already open
    if (dialog.open) return;

    fetch("/guess", {
      method: "POST",
      body: JSON.stringify({target: e.target.textContent.trim()}),
      headers: {"Content-Type": "application/json; charset=UTF-8"}
    })
      .then(r => r.json())
      .then(data => {
        if (data.correct) {
          // Keep it green when clicked
          e.target.className = "target cursor-default p-4 rounded-[15px] bg-gradient-to-br from-[#2ecc71] to-[#27ae60] text-white font-bold shadow-[0_4px_10px_rgba(0,0,0,0.1)] text-[0.9rem] sm:text-[1.1rem]";

          dialogText.innerText = data.message;
          nextBtn.classList.remove("hidden");
          dialog.showModal();

        } else {
          // Apply the red error styling and the shake animation
          e.target.className = "target cursor-not-allowed p-4 rounded-[15px] bg-red-500 text-white font-bold border-[3px] border-red-700 animate-shake shadow-[0_4px_10px_rgba(0,0,0,0.1)] text-[0.9rem] sm:text-[1.1rem]";
        }
      });
  });
});

nextBtn.addEventListener("click", function () {
  window.location.href = "/";
});
