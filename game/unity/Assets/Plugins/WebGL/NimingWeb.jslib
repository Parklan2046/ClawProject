mergeInto(LibraryManager.library, {
  NimingPrefersReducedMotion: function () {
    try {
      return window.matchMedia &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 1 : 0;
    } catch (error) {
      return 0;
    }
  }
});
