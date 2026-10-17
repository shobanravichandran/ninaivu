import { useEffect, useState } from "react";

// Node groups in fixed categorical order (validated palette: 8 slots, light and dark steps).
// Light-mode aqua/yellow/magenta sit below 3:1 contrast, so every node also gets a text label and
// the legend names each group: color is never the only cue.
export const GROUPS = [
  { key: "Customer", labels: ["Customer"], light: "#2a78d6", dark: "#3987e5", note: "who" },
  { key: "Issue", labels: ["Issue"], light: "#eb6834", dark: "#d95926", note: "shared state" },
  { key: "Fact", labels: ["Fact"], light: "#1baf7a", dark: "#199e70", note: "semantic" },
  { key: "Session", labels: ["Session"], light: "#eda100", dark: "#c98500", note: "episodic" },
  { key: "Handoff", labels: ["Handoff"], light: "#e87ba4", dark: "#d55181", note: "coordination" },
  { key: "Playbook", labels: ["Playbook"], light: "#008300", dark: "#008300", note: "procedural" },
  { key: "Agent", labels: ["Agent"], light: "#6250d6", dark: "#9085e9", note: "team" },
  { key: "Commerce", labels: ["Order", "Product", "Refund"], light: "#e34948", dark: "#e66767", note: "orders" },
] as const;

export const INK = {
  light: { primary: "#0b0b0b", secondary: "#52514e", link: "#c3c2b7", surface: "#fcfcfb" },
  dark: { primary: "#f0efec", secondary: "#c3c2b7", link: "#383835", surface: "#1a1a19" },
};

export function groupOf(label: string) {
  return GROUPS.find((g) => (g.labels as readonly string[]).includes(label)) ?? GROUPS[GROUPS.length - 1];
}

export function useDarkMode(): boolean {
  const query = "(prefers-color-scheme: dark)";
  const [dark, setDark] = useState(() => window.matchMedia(query).matches);
  useEffect(() => {
    const mql = window.matchMedia(query);
    const onChange = (e: MediaQueryListEvent) => setDark(e.matches);
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, []);
  return dark;
}
