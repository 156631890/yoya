document.querySelectorAll("[data-faq-button]").forEach((button) => {
  button.addEventListener("click", () => {
    const item = button.closest(".faq-item");
    const answer = item.querySelector(".faq-answer");
    const isHidden = answer.hasAttribute("hidden");
    document.querySelectorAll(".faq-answer").forEach((panel) => {
      panel.setAttribute("hidden", "");
    });
    if (isHidden) answer.removeAttribute("hidden");
  });
});

document.querySelectorAll("[data-year]").forEach((node) => {
  node.textContent = new Date().getFullYear();
});
