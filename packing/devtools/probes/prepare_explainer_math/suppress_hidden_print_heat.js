// Negative control for the print heat-map oracle. Print CSS lays out both certificates
// even though one retains its `hidden` attribute; suppressing that certificate's heat draw
// must make the visible-canvas/drawn-canvas comparison fail.
() => {
  const draw = CanvasRenderingContext2D.prototype.drawImage;
  CanvasRenderingContext2D.prototype.drawImage = /** @type {typeof draw} */ (
    /**
     * @this {CanvasRenderingContext2D}
     * @param {Parameters<typeof draw>} args
     */
    function (...args) {
      if (
        this.canvas.id.startsWith("prove-") &&
        this.canvas.closest(".cert-figure")?.hasAttribute("hidden")
      ) {
        return;
      }
      return draw.apply(this, args);
    }
  );
};
