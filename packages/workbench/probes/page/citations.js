// The citation data the page was built with, read from its own data block: the sha256 of the file
// it came from, or null where it was built without one, and per n the source of its lower and its
// upper bound where it cites either.
() => {
  const block = document.getElementById("atlas-data");
  if (block === null) {
    throw new Error("the page has no atlas-data block");
  }
  return JSON.parse(block.textContent ?? "null").citations ?? null;
};
