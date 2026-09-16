/* CoreText uses linear advances with native hinting. Select it before body paint;
   other platforms retain the explicit linear rendering policy below. */
if (navigator.platform.startsWith("Mac")) {
  document.documentElement.dataset.squaresNativeMathMetrics = "true";
}
