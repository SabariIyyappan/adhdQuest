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
  replan: ReplanEvent | null;
  reportId: string | null;
}

export function useSession(childId: string): SessionState {
  const [state, setState] = useState<SessionState>({
    gameUrl: null,
    levelCount: 0,
    replan: null,
    reportId: null,
  });

  useEffect(() => {
    return subscribeToSession(childId, (event) => {
      switch (event.event) {
        case "game_ready":
          setState((s) => ({ ...s, gameUrl: event.game_url, levelCount: event.level_count }));
          break;
        case "replan":
          setState((s) => ({ ...s, replan: event }));
          break;
        case "session_end":
          setState((s) => ({ ...s, reportId: event.report_id }));
          break;
      }
    });
  }, [childId]);

  return state;
}
