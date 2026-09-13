// Which of these ids are in the page? o.ids is the list to look for.
/** @param {{ids: string[]}} o */ (o) =>
  o.ids.filter(/** @param {string} id */ (id) => document.getElementById(id) !== null);
