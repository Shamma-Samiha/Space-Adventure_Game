document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("player-form");

  form.addEventListener("submit", (e) => {
    e.preventDefault();

    const name = form.name.value.trim();
    const age = form.age.value.trim();

    if (!name) {
      alert("Please enter your name.");
      form.name.focus();
      return;
    }
    if (!age || isNaN(age) || age < 1 || age > 99) {
      alert("Please enter a valid age between 1 and 99.");
      form.age.focus();
      return;
    }

    // For demonstration, just alert the values and reset form
    alert(`Welcome, ${name}! Age: ${age}`);

    // TODO: Add logic to start the game or pass data to the game

    form.reset();
  });
});
