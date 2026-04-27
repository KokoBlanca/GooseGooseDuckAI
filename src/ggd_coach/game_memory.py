from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class GameEvent:
    elapsed_seconds: int
    event_type: str
    player: str
    detail: str

    def display(self) -> str:
        minutes, seconds = divmod(self.elapsed_seconds, 60)
        who = self.player if self.player else "-"
        detail = f" | {self.detail}" if self.detail else ""
        return f"{minutes:02d}:{seconds:02d} [{self.event_type}] {who}{detail}"


@dataclass
class PlayerMemory:
    name: str
    suspicion: int = 0
    alive: bool = True
    last_seen: str = ""
    notes: list[str] = field(default_factory=list)

    def status(self) -> str:
        state = "alive" if self.alive else "dead"
        return f"{self.name}: suspicion={self.suspicion}, {state}, last={self.last_seen or '-'}"


class GameMemory:
    def __init__(self) -> None:
        self.started_at = datetime.now().astimezone()
        self.players: dict[str, PlayerMemory] = {}
        self.events: list[GameEvent] = []

    def reset(self) -> None:
        self.started_at = datetime.now().astimezone()
        self.players.clear()
        self.events.clear()

    def elapsed_seconds(self) -> int:
        return int((datetime.now().astimezone() - self.started_at).total_seconds())

    def add_event(self, event_type: str, player: str = "", detail: str = "") -> GameEvent:
        player = player.strip()
        detail = detail.strip()
        event = GameEvent(
            elapsed_seconds=self.elapsed_seconds(),
            event_type=event_type,
            player=player,
            detail=detail,
        )
        self.events.append(event)

        if player:
            memory = self.players.setdefault(player, PlayerMemory(name=player))
            self._apply_event(memory, event_type, detail)

        return event

    def _apply_event(self, player: PlayerMemory, event_type: str, detail: str) -> None:
        if event_type == "seen":
            player.last_seen = detail
        elif event_type == "suspicious":
            player.suspicion += 2
            if detail:
                player.notes.append(f"suspicious: {detail}")
        elif event_type == "cleared":
            player.suspicion = max(0, player.suspicion - 2)
            if detail:
                player.notes.append(f"cleared: {detail}")
        elif event_type == "dead":
            player.alive = False
        elif event_type == "claim" and detail:
            player.notes.append(f"claim: {detail}")

    def ranked_players(self) -> list[PlayerMemory]:
        return sorted(
            self.players.values(),
            key=lambda player: (player.alive, player.suspicion, player.name.lower()),
            reverse=True,
        )

    def suggestion(self) -> tuple[str, str]:
        alive_suspicious = [
            player for player in self.ranked_players() if player.alive and player.suspicion > 0
        ]
        if not alive_suspicious:
            return (
                "建议：继续收集信息，会议里先问位置；没有硬证据就跳票。",
                "目前没有被记录为可疑的存活玩家。",
            )

        top = alive_suspicious[0]
        if top.suspicion >= 4:
            return (
                f"建议：重点盘问 {top.name}；如果会议信息支持，可以投 {top.name}。",
                f"{top.name} 当前怀疑分最高：{top.suspicion}。",
            )

        return (
            f"建议：先问 {top.name} 的路线和任务，不急着强投。",
            f"{top.name} 有轻度可疑记录，但证据还不够硬。",
        )
