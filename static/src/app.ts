interface GuessResponse {
  correct: boolean;
  message?: string;
}

interface NextQuestionResponse {
  slur: string;
  targets: string[];
  correct_target: string;
  origin: string;
}

const targetsList = document.getElementById("targets-list") as HTMLUListElement | null;
const nextBtn = document.getElementById("next-btn") as HTMLButtonElement | null;
const dialog = document.getElementById("result-dialog") as HTMLDialogElement | null;
const dialogText = document.getElementById("dialog-text") as HTMLElement | null;
const slurElement = document.getElementById("current-slur") as HTMLElement | null;

let currentSlur = slurElement ? (slurElement.textContent?.trim() || "Unknown") : "Unknown";
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
function fireLevelStart() {
  window.dataLayer.push({
    event: "level_start",
    level_name: currentSlur
  });
}

fireLevelStart();

function attachTargetListeners() {
  const targets = document.querySelectorAll<HTMLElement>(".target");
  targets.forEach((target) => {
    target.addEventListener("click", handleTargetClick);
  });
}

function handleTargetClick(e: MouseEvent) {
  if (dialog && dialog.open) return;

  const targetEl = e.currentTarget as HTMLElement;
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
}

// Attach listeners initially
attachTargetListeners();

if (nextBtn) {
  nextBtn.addEventListener("click", function () {
    // Custom Funnel Event: Track when users successfully proceed to next question
    window.dataLayer.push({
      event: "next_question"
    });
    
    // SPA Fetch next question instead of reloading
    fetch("/next")
      .then(r => r.json() as Promise<NextQuestionResponse>)
      .then(data => {
        // Reset state
        guessAttempts = 0;
        levelEnded = false;
        currentSlur = data.slur;
        
        if (slurElement) {
          slurElement.textContent = currentSlur;
        }

        // Rebuild targets list dynamically
        if (targetsList) {
          targetsList.innerHTML = "";
          data.targets.forEach((targetStr) => {
            const li = document.createElement("li");
            li.className = "target cursor-pointer flex items-center p-4 rounded-none bg-white border-4 border-black text-black font-bold uppercase shadow-brutal transition-all duration-150 hover:bg-brutal-pink hover:text-white hover:shadow-brutal-hover active:shadow-brutal-active text-[1rem] sm:text-[1.2rem]";
            li.textContent = targetStr;
            targetsList.appendChild(li);
          });
          // Reattach click listeners to the newly created DOM elements
          attachTargetListeners();
        }

        // Reset UI
        if (dialog) dialog.close();
        if (nextBtn) nextBtn.classList.add("hidden");

        // Fire new level start
        fireLevelStart();
      })
      .catch(err => {
        console.error("Failed to fetch next question", err);
        // Fallback to full page reload if SPA fetch fails for any reason
        window.location.href = "/";
      });
  });
}
