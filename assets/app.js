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

document.querySelectorAll("[data-product-hero]").forEach((hero) => {
  const mainImage = hero.querySelector("[data-product-main-image]");
  const thumbs = [...hero.querySelectorAll("[data-product-thumb]")];
  if (!mainImage || thumbs.length === 0) return;

  thumbs.forEach((thumb) => {
    thumb.addEventListener("click", () => {
      const nextSrc = thumb.getAttribute("data-image");
      const nextAlt = thumb.getAttribute("data-alt") || mainImage.alt;
      if (!nextSrc) return;
      mainImage.src = nextSrc;
      mainImage.alt = nextAlt;
      thumbs.forEach((item) => item.classList.remove("is-active"));
      thumb.classList.add("is-active");
    });
  });
});
