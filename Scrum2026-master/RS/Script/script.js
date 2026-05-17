document.addEventListener("DOMContentLoaded", () => {
  const cards = document.querySelectorAll(".card");

  cards.forEach(card => {
    card.addEventListener("click", () => {
      const url = card.getAttribute("data-url");
      window.location.href = url;
    });
  });
});
