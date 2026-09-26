interface GuessResponse {
  correct: boolean;
  message?: string;
}

const targets = document.querySelectorAll<HTMLElement>(".target");
const nextBtn = document.getElementById("next-btn") as HTMLButtonElement | null;
const dialog = document.getElementById("result-dialog") as HTMLDialogElement | null;
const dialogText = document.getElementById("dialog-text") as HTMLElement | null;
const slurElement = document.getElementById("current-slur") as HTMLElement | null;
const currentSlur = slurElement ? (slurElement.textContent?.trim() || "Unknown") : "Unknown";

let guessAttempts = 0;
let levelEnded = false;

declare global {
  interface Window {
    dataLayer: any[];
  }
}

// Initialize dataLayer if it doesn't exist
window.dataLayer = window.dataLayer || [];

// GA4 Recommended Event: level_start
// Fired when the page loads and a new question appears
window.dataLayer.push({
  event: "level_start",
  level_name: currentSlur
});

targets.forEach((target) => {
  target.addEventListener("click", function (e: MouseEvent) {
    // Prevent multiple clicks if dialog is already open
    if (dialog && dialog.open) return;

    const targetEl = e.target as HTMLElement;
    const clickedTarget = targetEl.textContent?.trim() || "";
    guessAttempts++;

    fetch("/guess", {
      method: "POST",
      body: JSON.stringify({ target: clickedTarget }),
      headers: { "Content-Type": "application/json; charset=UTF-8" }
    })
      .then(r => r.json() as Promise<GuessResponse>)
      .then(data => {
        // Custom Event: select_answer (Deep insight into wrong guesses)
        window.dataLayer.push({
          event: "select_answer",
          slur: currentSlur,
          chosen_target: clickedTarget,
          correct: data.correct,
          attempt_number: guessAttempts
        });

        if (data.correct) {
          // Keep it green when clicked
          targetEl.className = "target cursor-default p-4 rounded-none bg-brutal-green border-4 border-black text-black font-bold shadow-brutal text-[1rem] sm:text-[1.2rem] uppercase";

          if (dialogText) dialogText.innerText = data.message || "";
          if (nextBtn) nextBtn.classList.remove("hidden");
          if (dialog) dialog.showModal();

          if (!levelEnded) {
            levelEnded = true;
            // GA4 Recommended Event: level_end
            // Fired exclusively when they solve the level
            window.dataLayer.push({
              event: "level_end",
              level_name: currentSlur,
              success: true,
              attempts: guessAttempts
            });
          }

        } else {
          // Apply the red error styling and the shake animation
          targetEl.className = "target cursor-not-allowed p-4 rounded-none bg-red-500 border-4 border-black text-white font-bold animate-shake shadow-brutal text-[1rem] sm:text-[1.2rem] uppercase";
        }
      })
      .catch(err => console.error("Guess request failed", err));
  });
});

if (nextBtn) {
  nextBtn.addEventListener("click", function () {
    // Custom Funnel Event: Track when users successfully proceed to next question
    window.dataLayer.push({
      event: "next_question"
    });
    window.location.href = "/";
  });
}
