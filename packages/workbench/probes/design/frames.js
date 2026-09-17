// Resolve after two animation frames, so a layout the last click or resize queued has applied.
() =>
  new Promise((resolve) => {
    requestAnimationFrame(() => requestAnimationFrame(() => resolve(true)));
  });
