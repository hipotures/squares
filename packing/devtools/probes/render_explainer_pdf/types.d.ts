// What the PDF exporter's math trace probes pass between them.

/** A visible prepared Text node, and the identity a snapshot gives it. */
interface SquaresSelectedText {
  node: Text;
  formula: number;
  token: number;
  path: string;
}

/** `render_explainer_pdf/math_snapshot`: the visible prepared math at one phase. */
interface SquaresMathSnapshot {
  phase: string;
  time_ms: number;
  font_status: FontFaceSetLoadStatus;
  fonts: object[];
  token_limit: number;
  truncated: boolean;
  formulas: object[];
  tokens: object[];
}

/** The snapshot function `math_snapshot.js` returns. */
type SquaresMathSnapshotter = (
  phase: string,
  selected?: SquaresSelectedText[] | null,
) => SquaresMathSnapshot;

/** One change `render_explainer_pdf/print_activity` saw while a print was in flight. */
interface SquaresPrintActivityRecord {
  at_ms: number;
  kind: string;
  where: string;
  detail: string;
}

/** The watch `print_activity.js` installs, closed and read by `print_activity_report.js`. */
interface SquaresPrintActivity {
  records: SquaresPrintActivityRecord[];
  limit: number;
  truncated: boolean;
  status: FontFaceSetLoadStatus;
  note: (mutation: MutationRecord) => void;
  stop: () => void;
}
