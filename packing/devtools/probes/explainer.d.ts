// The explainer page's globals, as the probes under `packing/devtools/probes` and
// `packing/tests/probes` read them. Two kinds live here: the page's own API (kpress's math
// runtime and the host adapter `render_explainer` inlines).
//
// A probe group's own instrumentation globals belong in a `.d.ts` in that group's
// directory. Extend an interface declared here by merging, in your own file; never declare a
// `var` a second time.

/** The host adapter `render_explainer`'s `host_math_init` installs as `squaresMath`. */
interface SquaresMathHost {
  render(el: Element, source: string, display?: boolean): Promise<boolean>;
  reserve(): () => void;
  batch(jobs: ReadonlyArray<() => unknown>): Promise<void>;
  submitted(): Promise<void>;
  settled(): Promise<void>;
  context: { isSansContext(node: Node): boolean };
}

/** kpress's math runtime, `katex/katex-math-runtime.js`. */
interface KpressMathText {
  ready(nodes?: Iterable<Element>, options?: object): Promise<unknown>;
  render(tex: string, node: Element, katexOptions?: object, options?: object): Promise<unknown>;
  hydrate(tex: string, node: Element, katexOptions?: object, options?: object): Promise<unknown>;
  installTablesFor(node: Element, options?: object): unknown;
  restore(): void;
  complete(): void;
}

/**
 * The KaTeX build the page inlines: its public `render`, which `check_math_faces` re-typesets
 * with and the startup fixture stands in for. A checker that uses an internal method extends
 * this interface in its own declaration file.
 */
interface SquaresKatex {
  render(expression: string, element: Element, options?: object): void;
}

declare var katex: SquaresKatex;
declare var squaresMath: SquaresMathHost | undefined;
declare var kpressMathText: KpressMathText | undefined;
