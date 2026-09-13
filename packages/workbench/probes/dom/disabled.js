// The `disabled` property of the element with this id.
/** @param {{id: string}} o */ (o) =>
  /** @type {HTMLButtonElement | HTMLInputElement | HTMLSelectElement} */ (
    document.getElementById(o.id)
  ).disabled;
