from otree.api import Bot, Submission, SubmissionMustFail, expect
from . import *


class PlayerBot(Bot):
    def play_round(self):
        yield Submission(Stage1Instructions, check_html=False)
        expect('240', 'in', self.html)
        expect('Screener 1 out of 3', 'in', self.html)
        yield Submission(QuantInstructions, check_html=False)
        yield Submission(OptRound1, dict(opt1_focus_lost=1, opt1_copy_paste=0), check_html=False)
        yield Submission(OptAgain2, check_html=False)
        yield Submission(OptRound2, dict(opt2_focus_lost=0, opt2_copy_paste=2), check_html=False)
        yield Submission(OptAgain3, check_html=False)
        yield Submission(OptRound3, dict(opt3_focus_lost=0, opt3_copy_paste=0), check_html=False)
        # round 1: final answer at the maximum -> score 1; rounds 2, 3: final answer 0
        expect(self.player.opt1_score, 1.0)
        expect(len(json.loads(self.player.opt1_guesses)), opt.MAX_GUESSES)
        expect(self.player.opt2_final, 0)
        expect(0 <= self.player.opt2_score < 1, True)
        expect(self.player.quant_score, round((1 + self.player.opt2_score + self.player.opt3_score) / 3, 4))
        expect(self.player.quant_focus_lost, 1)
        expect(self.player.quant_copy_paste, 2)
        yield QuantBeliefs, dict(quant_belief_score=70, quant_belief_pct=60)
        yield Submission(ErrorInstructions, check_html=False)
        yield ErrorTask, {t['key']: str(t['correct']) for t in ERROR_TABLES}
        # the live-method checks above leave a cached copy of the player in the bot
        from otree.database import db
        db.expire_all()
        expect(self.player.error_score, 10)
        yield ErrorBeliefs, dict(error_belief_correct=5, error_belief_pct=40)
        yield Submission(CommInstructions, check_html=False)
        yield CommTask, dict(comm_headline='Bonus + monitoring improves accuracy', comm_summary='...')
        yield CommBeliefs, dict(comm_belief_correct=8, comm_belief_pct=70)
        yield AttentionCheck2, dict(attention_check_2=2)
        expect(self.participant.attention_fails, 1 if self.player.id_in_group == 1 else 0)
        yield Submission(EndStage1, check_html=False)


def call_live_method(method, page_class, **kwargs):
    import asyncio
    raw = method

    def call(pid, payload):  # oTree 6 returns an async generator here
        async def first():
            async for r in raw(pid, payload):
                return r
        return asyncio.new_event_loop().run_until_complete(first())[pid]

    name = page_class.__name__
    for pid in [p.id_in_group for p in kwargs['group'].get_players()]:
        if name == 'QuantInstructions':
            r = call(pid, dict(type='guess', guess=240))
            expect(r['type'], 'result')
            expect(r['result'], opt.value('t1', 240))
            expect(call(pid, dict(type='guess', guess=301))['type'], 'error')
        elif name.startswith('OptRound'):
            rnd = int(name[-1])
            fn = opt.ROUND_FUNCTIONS[rnd - 1]
            # no final answer before all guesses are used
            expect(call(pid, dict(type='final', guess=10))['type'], 'error')
            expect(call(pid, dict(type='guess', guess=-1))['type'], 'error')
            for i in range(opt.MAX_GUESSES):
                r = call(pid, dict(type='guess', guess=i * 20))
                expect(r['result'], opt.value(fn, i * 20))
            # 16th guess is refused (only the final answer is allowed now)
            expect(call(pid, dict(type='guess', guess=5))['type'], 'error')
            final = opt.STATS[fn]['xmax'] if rnd == 1 else 0
            expect(call(pid, dict(type='final', guess=final))['type'], 'final_saved')
            expect(call(pid, dict(type='guess', guess=5))['type'], 'done')
