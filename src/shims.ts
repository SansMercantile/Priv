if (typeof window !== "undefined") {
  try {
    const originalFetch = window.fetch;
    if (originalFetch) {
      let currentFetch = originalFetch;

      // Check if window.fetch can be redefined or if we need to wrap it on the instance
      const descriptor = Object.getOwnPropertyDescriptor(window, "fetch") || 
                         Object.getOwnPropertyDescriptor(Object.getPrototypeOf(window), "fetch");

      if (!descriptor || descriptor.configurable !== false) {
        Object.defineProperty(window, "fetch", {
          get() {
            return currentFetch;
          },
          set(val) {
            currentFetch = val;
          },
          configurable: true,
          enumerable: true,
        });
        console.log("[SANS Shim] Successfully configured writable getter/setter for window.fetch.");
      } else {
        console.warn("[SANS Shim] window.fetch is not configurable.");
      }
    }
  } catch (error) {
    console.warn("[SANS Shim] Failed to install window.fetch compatibility shim:", error);
  }
}
export {};
