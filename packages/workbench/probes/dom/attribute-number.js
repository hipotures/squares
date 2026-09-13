// One attribute of the element with this id, as a number. o.name is the attribute.
/** @param {{id: string, name: string}} o */
(o) => {
  const element = document.getElementById(o.id);
  if (element == null) {
    throw new Error(`probe requires #${o.id}`);
  }
  return Number(element.getAttribute(o.name));
};
