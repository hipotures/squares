// The legend sentence's letters that stand on the baseline, for reading where their ink ends:
// each one's horizontal extent in viewport px, whether it is math or text, and the sentence's
// line box. Only letters with no descender count, since a descender's ink ends below the line
// by design. Found with a Range per character, which reports the glyph's advance box; KaTeX's
// MathML copy is skipped, being clipped out of sight. Null where the legend is not drawn.
() => {
  const sentence = document.querySelector("#stage-note .note-sentence");
  if (sentence === null || sentence.getClientRects().length === 0) {
    return null;
  }
  const onBaseline = /[abcdefhiklmnorstuvwxz]/;
  const line = sentence.getBoundingClientRect();
  /** @type {{char: string, math: boolean, left: number, right: number}[]} */
  const glyphs = [];
  const walker = document.createTreeWalker(sentence, NodeFilter.SHOW_TEXT);
  for (let node = walker.nextNode(); node !== null; node = walker.nextNode()) {
    const parent = node.parentElement;
    if (parent === null || parent.closest(".katex-mathml") !== null) {
      continue;
    }
    const math = parent.closest(".note-math") !== null;
    const text = node.textContent ?? "";
    for (let index = 0; index < text.length; index += 1) {
      const char = text.charAt(index);
      if (!onBaseline.test(char)) {
        continue;
      }
      const range = document.createRange();
      range.setStart(node, index);
      range.setEnd(node, index + 1);
      const box = range.getBoundingClientRect();
      glyphs.push({ char, math, left: box.left, right: box.right });
    }
  }
  return {
    line: { left: line.left, top: line.top, right: line.right, bottom: line.bottom },
    glyphs,
  };
};
