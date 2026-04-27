from __future__ import annotations

from .models import GameState, Observation, Suggestion


class SuggestionEngine:
    def suggest(self, observation: Observation) -> Suggestion:
        if observation.state == GameState.MEETING:
            return Suggestion(
                action="ask_or_skip",
                confidence=0.5,
                message="信息不足时先提问；如果没人有强证据，建议跳票。",
                reason="会议阶段需要基于发言和时间线判断，当前还没有语音记录。",
            )

        if observation.state == GameState.VOTING:
            return Suggestion(
                action="skip_vote",
                confidence=0.5,
                message="没有可靠矛盾记录时，建议跳票。",
                reason="投票建议需要玩家发言、目击和死亡时间线支持。",
            )

        if observation.state == GameState.FREE_MOVEMENT:
            return Suggestion(
                action="observe",
                confidence=0.4,
                message="继续观察，优先记录附近玩家、任务和异常事件。",
                reason="Coach 第一版暂不控制移动，只记录信息。",
            )

        return Suggestion(
            action="pause",
            confidence=0.8,
            message="当前状态未知，先暂停并等待更多画面信息。",
            reason="未知界面默认保守处理，避免误导或误操作。",
        )
