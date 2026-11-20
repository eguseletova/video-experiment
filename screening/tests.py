from otree.api import Bot, Submission, expect
from . import *


class PlayerBot(Bot):
    def play_round(self):
        yield Submission(Stage1Instructions, check_html=False)
        yield Submission(QuantInstructions, check_html=False)
        yield QuantTask, {q['key']: q['correct'] for q in QUANT_QUESTIONS}
        expect(self.player.quant_score, 10)
        yield QuantBeliefs, dict(quant_belief_correct=7, quant_belief_pct=60)
        yield Submission(ErrorInstructions, check_html=False)
        yield ErrorTask, {t['key']: str(t['correct']) for t in ERROR_TABLES}
        expect(self.player.error_score, 10)
        yield ErrorBeliefs, dict(error_belief_correct=5, error_belief_pct=40)
        yield Submission(CommInstructions, check_html=False)
        yield CommTask, dict(comm_headline='Bonus + monitoring improves accuracy', comm_summary='...')
        yield CommBeliefs, dict(comm_belief_correct=8, comm_belief_pct=70)
        yield AttentionCheck2, dict(attention_check_2=2)
        expect(self.participant.attention_fails, 1 if self.player.id_in_group == 1 else 0)
        yield Submission(EndStage1, check_html=False)
