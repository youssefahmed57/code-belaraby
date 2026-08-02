"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";

export function HashScrollHandler() {
  const pathname = usePathname();

  useEffect(() => {
    const scrollToHash = () => {
      const id = decodeURIComponent(window.location.hash.slice(1));
      if (!id) return;

      requestAnimationFrame(() => {
        const element = document.getElementById(id);
        if (!element) return;

        element.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      });
    };

    scrollToHash();
    window.addEventListener("hashchange", scrollToHash);

    return () => {
      window.removeEventListener("hashchange", scrollToHash);
    };
  }, [pathname]);

  return null;
}
