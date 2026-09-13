// How many elements a removed stack's selector still matches. Takes {selector}.
/** @param {{selector: string}} o */ (o) => document.querySelectorAll(o.selector).length;
