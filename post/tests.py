from otree.api import Bot, Submission, SubmissionMustFail, expect
from . import *


class PlayerBot(Bot):
    def play_round(self):
        yield SubmissionMustFail(Demographics, dict(education=5, gender=2, shl=2))
        yield SubmissionMustFail(Demographics, dict(education=5, gender=2, shl=2, race_5=True, race_7=True))
        yield Demographics, dict(age='30', education=5, gender=4, gender_text='x', shl=2, race_5=True)
        lsas = {}
        for i in range(1, 25):
            lsas[f'lsas_fear_{i}'] = 1
            lsas[f'lsas_avoid_{i}'] = 2
        yield LSAS1, {k: v for k, v in lsas.items() if int(k.rsplit('_', 1)[1]) <= 8}
        yield LSAS2, {k: v for k, v in lsas.items() if 9 <= int(k.rsplit('_', 1)[1]) <= 16}
        yield LSAS3, {k: v for k, v in lsas.items() if int(k.rsplit('_', 1)[1]) >= 17}
        expect(self.player.lsas_total, 72)
        expect(self.player.lsas_fear_total, 24)
        expect(self.player.lsas_performance_total + self.player.lsas_social_total, 72)
        # all "Very accurate" (5): reversed items 2 and 4 score 1 -> 8*5 + 2*1 = 42
        yield Submission(Neuroticism, {f'neuro_{i}': 5 for i in range(1, 11)}, check_html=False)
        expect(self.player.neuro_total, 42)
        # all "Strongly agree" (4): positive items 3 each (5 items) + negative items 0 -> 15
        yield Submission(Rosenberg, {f'rses_{i}': 4 for i in range(1, 11)}, check_html=False)
        expect(self.player.rses_total, 15)
        yield Submission(GAD7, {**{f'gad_{i}': 2 for i in range(1, 8)}, 'gad_difficulty': 2}, check_html=False)
        expect(self.player.gad_total, 14)
        yield Exit, dict(comments='', video_consent=4)
        yield Submission(Redirect, check_html=False)
