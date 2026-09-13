// Is a removed element back in the page? Takes {id}.
/** @param {{id: string}} o */ (o) => document.getElementById(o.id) !== null;
