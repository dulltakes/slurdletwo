const targets = document.querySelectorAll(".target");
const nextBtn = document.getElementById("next-btn");

targets.forEach(target => {
  target.addEventListener("click", function (e) {
    fetch("http://127.0.0.1:5001/guess", {
      method: "POST",
      body: JSON.stringify({target: e.target.textContent}),
      headers: {"Content-Type": "application/json; charset=UTF-8"}
    })
      .then(r => r.json())
      .then(data => {
        if (data.correct) {
          document.getElementById("result").textContent = data.message;
          nextBtn.style.display = "block";
        } else {
          e.target.style.color = "red";
        }
      });
  });
});

nextBtn.addEventListener("click", function () {
  window.location.href = "/next";
});
