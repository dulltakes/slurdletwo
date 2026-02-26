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
          e.target.className = "target p-4 border-2 rounded-xl text-center text-lg font-bold select-none bg-green-100 border-green-500 text-green-800";

          // Just update the text and show the existing dialog
          dialogText.innerText = data.message;
          nextBtn.classList.remove("hidden");
          dialog.showModal();

        } else {
          e.target.className = "target p-4 border-2 rounded-xl text-center text-lg font-medium select-none bg-red-50 border-red-300 text-red-500 cursor-not-allowed";
        }
      });
  });
});

nextBtn.addEventListener("click", function () {
  window.location.href = "/";
});
