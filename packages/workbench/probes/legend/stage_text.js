// The stage's whole text, as a viewer would read it off a still.
() => {
  const stage = document.getElementById("stage");
  if (stage == null) {
    throw new Error("probe requires #stage");
  }
  return stage.innerText.replace(/\s+/g, " ");
};
