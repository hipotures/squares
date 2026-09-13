// Which pieces of the chooser are hidden. o.ids is the list to ask about.
/** @param {{ids: string[]}} o */
(o) =>
  o.ids.map((id) => {
    const element = document.getElementById(id);
    if (element == null) {
      throw new Error(`probe requires #${id}`);
    }
    return [id, element.hidden];
  });
