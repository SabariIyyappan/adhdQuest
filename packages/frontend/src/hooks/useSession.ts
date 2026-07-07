/**
 * useSession — subscribe to a child's realtime session channel and expose the
 * latest game URL, replan overlay state, and end signal (Contract C).
 */

import { useEffect, useState } from "react";
import type { ReplanEvent } from "@adhdquest/contracts";
import { subscribeToSession } from "../lib/butterbase";

export interface SessionState {
  gameUrl: string | null;
  levelCount: number;
  currentLevelIndex: number;
  replan: ReplanEvent | null;
  reportId: string | null;
  sessionId: string | null;
}

export function useSession(childId: string): SessionState {
  const [state, setState] = useState<SessionState>({
    gameUrl: null,
    levelCount: 0,
    currentLevelIndex: 1,
    replan: null,
    reportId: null,
    sessionId: null,
  });

  useEffect(() => {
    if (!childId || childId === "TODO-selected-child") return;

    return subscribeToSession(childId, (event) => {
      switch (event.event) {
        case "game_ready":
          setState((s) => ({
            ...s,
            gameUrl: event.game_url,
            levelCount: event.level_count,
            currentLevelIndex: 1,
          }));
          break;
        case "replan":
          setState((s) => ({
            ...s,
            replan: event,
            currentLevelIndex: event.trigger_level, // Replan is triggered at a specific level
          }));
          break;
        case "session_end":
          setState((s) => ({
            ...s,
            reportId: event.report_id,
            sessionId: event.session_id,
          }));
          break;
      }
    });
  }, [childId]);

  // Set up message listener for events postMessage'd from Daytona iframe game
  useEffect(() => {
    function handleGameMessage(e: MessageEvent) {
      // Expect game to send messages like: { type: 'level_complete', next_level: 3 }
      if (e.data && typeof e.data === "object") {
        if (e.data.type === "level_complete" || e.data.type === "level_start") {
          setState((s) => ({
            ...s,
            currentLevelIndex: typeof e.data.level === "number" ? e.data.level : s.currentLevelIndex + 1,
          }));
        }
      }
    }

    window.addEventListener("message", handleGameMessage);
    return () => window.removeEventListener("message", handleGameMessage);
  }, []);

  return state;
}
