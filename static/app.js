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
          e.target.className = "target cursor-default p-4 rounded-none bg-brutal-green border-4 border-black text-black font-bold shadow-brutal text-[1rem] sm:text-[1.2rem] uppercase";

          dialogText.innerText = data.message;
          nextBtn.classList.remove("hidden");
          dialog.showModal();

        } else {
          // Apply the red error styling and the shake animation
          e.target.className = "target cursor-not-allowed p-4 rounded-none bg-red-500 border-4 border-black text-white font-bold animate-shake shadow-brutal text-[1rem] sm:text-[1.2rem] uppercase";
        }
      });
  });
});

nextBtn.addEventListener("click", function () {
  window.location.href = "/";
});
