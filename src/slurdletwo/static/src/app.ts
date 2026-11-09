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
const cookieBanner = document.getElementById("cookie-banner") as HTMLElement | null;
const consentYesBtn = document.getElementById("consent-yes-btn") as HTMLButtonElement | null;
const consentNoBtn = document.getElementById("consent-no-btn") as HTMLButtonElement | null;

const CONSENT_STORAGE_KEY = "dt_cookie_consent";

const BASE_PATH = "/slurdle";

let currentSlur = slurElement ? (slurElement.textContent?.trim() || "Unknown") : "Unknown";
if (currentSlur && currentSlur !== "Unknown") {
  document.title = currentSlur;
}
let guessAttempts = 0;
let levelEnded = false;

declare global {
  interface Window {
    dataLayer: any[];
    gtag?: (...args: any[]) => void;
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

function toSmartQuotes(text: string): string {
  if (!text) return "";
  return text
    .replace(/(^|[\s(\[{<—\-])"(\S)/g, "$1“$2")
    .replace(/"/g, "”");
}

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

  fetch(`${BASE_PATH}/guess`, {
    method: "POST",
    body: JSON.stringify({ target: clickedTarget, slur: currentSlur }),
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

        if (dialogText) dialogText.innerText = toSmartQuotes(data.message || "");
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
    fetch(`${BASE_PATH}/next`)
      .then(r => r.json() as Promise<NextQuestionResponse>)
      .then(data => {
        // Reset state
        guessAttempts = 0;
        levelEnded = false;
        currentSlur = data.slur;
        document.title = currentSlur;
        
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
        window.location.href = `${BASE_PATH}/`;
      });
  });
}

function handleConsentUpdate(granted: boolean): void {
  const status = granted ? "granted" : "denied";
  try {
    localStorage.setItem(CONSENT_STORAGE_KEY, status);
  } catch (err) {
    console.warn("Unable to save consent preference to localStorage", err);
  }

  // 1. Update Google Consent Mode v2
  if (typeof window.gtag === "function") {
    window.gtag("consent", "update", {
      ad_storage: status,
      ad_user_data: status,
      ad_personalization: status,
      analytics_storage: status,
    });
  }

  // 2. Push event to dataLayer
  window.dataLayer.push({
    event: "cookie_consent_update",
    consent_status: status,
    consent_analytics: status,
    consent_marketing: status,
  });

  // 3. Dismiss banner
  if (cookieBanner) {
    cookieBanner.classList.add("hidden");
  }
}

// Show cookie banner if user has not yet decided
try {
  if (cookieBanner && !localStorage.getItem(CONSENT_STORAGE_KEY)) {
    cookieBanner.classList.remove("hidden");
  }
} catch {
  if (cookieBanner) {
    cookieBanner.classList.remove("hidden");
  }
}

if (consentYesBtn) {
  consentYesBtn.addEventListener("click", () => handleConsentUpdate(true));
}

if (consentNoBtn) {
  consentNoBtn.addEventListener("click", () => handleConsentUpdate(false));
}
