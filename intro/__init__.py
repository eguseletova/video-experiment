from otree.api import *
import walkthrough
import random

doc = """
Qualtrics blocks: Consent -> Camera Microphone Check -> Introduction.
Participants who do not consent, or whose audio/video check fails,
are shown an end-of-survey message and cannot continue.
"""

YES_NO = [[1, 'Yes'], [2, 'No']]


class C(BaseConstants):
    NAME_IN_URL = 'intro'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    # Qualtrics QID15 "ID_generator": one of 10000..10322, evenly presented
    WORKER_IDS = list(range(10000, 10323))


class Subsession(BaseSubsession):
    pass


def creating_session(subsession: Subsession):
    for p in subsession.get_players():
        p.participant.attention_fails = 0
    # Even presentation of worker IDs: shuffle the pool and deal it out.
    pool = C.WORKER_IDS.copy()
    random.shuffle(pool)
    for i, p in enumerate(subsession.get_players()):
        p.participant.workerid = str(pool[i % len(pool)])
        p.workerid = p.participant.workerid


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # --- Consent (QID38-40) ---
    consent_age = models.IntegerField(
        label='I am age 18 or older.', choices=YES_NO, widget=widgets.RadioSelect
    )
    consent_understand = models.IntegerField(
        label='I have read and understand the information above.',
        choices=YES_NO,
        widget=widgets.RadioSelect,
    )
    consent_participate = models.IntegerField(
        label='I want to participate in this research and continue with the survey.',
        choices=YES_NO,
        widget=widgets.RadioSelect,
    )

    # --- Important information (QID5), not forced in Qualtrics ---
    q5_requirements = models.IntegerField(
        choices=[
            [1, 'Yes, I confirm that I meet the requirements above and agree to participate in the study.'],
            [2, 'No, I do not wish to continue.'],
        ],
        widget=widgets.RadioSelect,
        blank=True,
    )

    # --- Camera & microphone check (QID2), embedded data av_test_confirm ---
    av_test_confirm = models.StringField(blank=True)

    # --- Prolific ID (QID87) + hidden worker ID (QID15) ---
    prolific_id = models.StringField(label='Prolific ID')
    workerid = models.StringField(blank=True)

    # --- Attention check 1 (instructed response: correct answer = 5 'None of the above') ---
    attention_check_1 = models.IntegerField(
        choices=[
            [1, 'Reading'],
            [2, 'Sports'],
            [3, 'Cooking'],
            [4, 'Travelling'],
            [5, 'None of the above'],
        ],
        widget=widgets.RadioSelect,
    )
    attention_check_1_passed = models.BooleanField()


def consented(player: Player):
    return (
        player.consent_age == 1
        and player.consent_understand == 1
        and player.consent_participate == 1
    )


# PAGES
class Consent(Page):
    form_model = 'player'
    form_fields = ['consent_age', 'consent_understand', 'consent_participate']


class ConsentDeclined(Page):
    """Qualtrics End of Survey (message MS_5ABrPKHNvO3Kmx0)."""

    screen_out = True

    @staticmethod
    def is_displayed(player: Player):
        return not consented(player)


class StudyInfo(Page):
    form_model = 'player'
    form_fields = ['q5_requirements']


class AVCheck(Page):
    form_model = 'player'
    form_fields = ['av_test_confirm']


class AVFailed(Page):
    """Qualtrics End of Survey (message MS_eA5o1b1IIV3k3NY)."""

    screen_out = True

    @staticmethod
    def is_displayed(player: Player):
        return player.field_maybe_none('av_test_confirm') != 'yes'


class Introduction(Page):
    pass


class ProlificID(Page):
    form_model = 'player'
    form_fields = ['prolific_id']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(default_pid=player.participant.label or '')


class AttentionCheck1(Page):
    form_model = 'player'
    form_fields = ['attention_check_1']

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if walkthrough.is_on(player):
            return
        player.attention_check_1_passed = player.attention_check_1 == 5
        if not player.attention_check_1_passed:
            player.participant.attention_fails += 1


class AttentionFailed(Page):
    """Screen-out once the participant has failed too many attention checks."""

    template_name = 'global/AttentionFailed.html'
    screen_out = True

    @staticmethod
    def is_displayed(player: Player):
        return player.participant.attention_fails >= player.session.config['attention_fails_to_exclude']


page_sequence = [
    Consent,
    ConsentDeclined,
    StudyInfo,
    AVCheck,
    AVFailed,
    Introduction,
    ProlificID,
    AttentionCheck1,
    AttentionFailed,
]

walkthrough.apply(page_sequence)
