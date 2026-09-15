// The page globals `compare_math_fonts`'s probes read: the KaTeX build the variant page
// inlines, through the internal entry point that returns its box tree before it is drawn.

/** One node of KaTeX's box tree: a symbol carries its text and metric widths. */
interface CompareMathFontsKatexNode {
  text?: unknown;
  width?: unknown;
  italic?: number;
  children?: CompareMathFontsKatexNode[];
}

/** The root of a tree `__renderToDomTree` builds, which draws itself as a DOM node. */
interface CompareMathFontsKatexTree extends CompareMathFontsKatexNode {
  toNode(): Node;
}

interface CompareMathFontsKatex {
  __renderToDomTree(
    expression: string,
    options: { throwOnError: boolean; displayMode: boolean },
  ): CompareMathFontsKatexTree;
}

declare var katex: CompareMathFontsKatex;
