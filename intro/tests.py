from otree.api import Bot, Submission, expect
from . import *


class PlayerBot(Bot):
    def play_round(self):
        yield Consent, dict(consent_age=1, consent_understand=1, consent_participate=1)
        yield StudyInfo, dict(q5_requirements=1)
        yield AVCheck, dict(av_test_confirm='yes')
        yield Submission(Introduction, check_html=False)
        yield ProlificID, dict(prolific_id='TESTPID')
        # first bot fails attention check 1 (not excluded: threshold is 2)
        yield AttentionCheck1, dict(attention_check_1=5 if self.player.id_in_group > 1 else 1)
        expect(self.player.attention_check_1_passed, self.player.id_in_group > 1)
