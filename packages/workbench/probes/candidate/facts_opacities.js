// How far in each of the panel's two fading layers is.
() =>
  ["facts-a", "facts-b"].map((id) => {
    const element = document.getElementById(id);
    if (element == null) {
      throw new Error(`probe requires #${id}`);
    }
    return parseFloat(element.style.opacity);
  });
