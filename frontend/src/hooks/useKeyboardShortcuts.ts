import { useEffect } from "react";

interface ShortcutHandlers {
  onNewChat: () => void;
  onToggleSidebar: () => void;
  onFocusInput: () => void;
  onSearch: () => void;
}

export function useKeyboardShortcuts({
  onNewChat,
  onToggleSidebar,
  onFocusInput,
  onSearch,
}: ShortcutHandlers) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const ctrl = e.ctrlKey || e.metaKey;
      const tag = (e.target as HTMLElement)?.tagName?.toLowerCase();
      const isInput = tag === "input" || tag === "textarea" || (e.target as HTMLElement)?.isContentEditable;

      // Ctrl+N — nuevo chat (no en inputs)
      if (ctrl && e.key === "n" && !isInput) {
        e.preventDefault();
        onNewChat();
        return;
      }

      // Ctrl+B — toggle sidebar
      if (ctrl && e.key === "b") {
        e.preventDefault();
        onToggleSidebar();
        return;
      }

      // Ctrl+K — abrir búsqueda
      if (ctrl && e.key === "k") {
        e.preventDefault();
        onSearch();
        return;
      }

      // / — enfocar input del chat (no en inputs)
      if (e.key === "/" && !isInput) {
        e.preventDefault();
        onFocusInput();
        return;
      }
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onNewChat, onToggleSidebar, onFocusInput, onSearch]);
}
