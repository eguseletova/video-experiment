from otree.api import *
import walkthrough
import random
import json
from . import optimization as opt

doc = """
Stage 1: Screening (Qualtrics group "Screening Tasks").
Quantitative Analysis = Optimization task of Weidmann & Deming (practice + 3
untimed rounds, see optimization.py) -> beliefs, Error Detection (2 min) ->
beliefs, Research Communication (3 min) -> beliefs, End of Stage 1.
Error Detection table order is randomized (Qualtrics "RandomizeAll").
"""

IMG = '/static/global/img/'


# Qualtrics QID52, 62-70 (export tags Q52, Q62..Q70): 7x7 tables of 0/1.
ERROR_TABLES = [
    dict(key='err_q52', rows=['1010010', '0101001', '1100100', '0010110', '1001001', '0110010', '0001101']),
    dict(key='err_q62', rows=['0011000', '1001010', '0000000', '1000110', '0101001', '1010100', '0000000']),
    dict(key='err_q63', rows=['1110001', '0010110', '1001001', '0100100', '1010010', '0101001', '0010100']),
    dict(key='err_q64', rows=['0001101', '1000000', '0100101', '1001000', '0000001', '1100000', '0011001']),
    dict(key='err_q65', rows=['1000110', '0110001', '1000010', '0100100', '0000011', '0001100', '1100010']),
    dict(key='err_q66', rows=['0100101', '1010010', '0101001', '0010100', '0001010', '0100101', '1010010']),
    dict(key='err_q67', rows=['0000000', '0100000', '0001001', '0000010', '0001000', '0000010', '0100000']),
    dict(key='err_q68', rows=['0010101', '1100010', '0011001', '1000100', '0101010', '1010001', '0100110']),
    dict(key='err_q69', rows=['1001010', '0100101', '1010010', '0100101', '1000010', '0010100', '1000001']),
    dict(key='err_q70', rows=['0100010', '1010101', '0100000', '1000001', '0000100', '1000000', '0010000']),
]
for t in ERROR_TABLES:
    t['correct'] = sum(r.count('1') for r in t['rows'])


class C(BaseConstants):
    NAME_IN_URL = 'screening'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    ERROR_SECONDS = 120
    COMM_SECONDS = 180


class Subsession(BaseSubsession):
    pass


def creating_session(subsession: Subsession):
    for p in subsession.get_players():
        e_order = list(range(len(ERROR_TABLES)))
        random.shuffle(e_order)
        p.error_order = ','.join(ERROR_TABLES[i]['key'] for i in e_order)


class Group(BaseGroup):
    pass


def belief_correct_field(label):
    return models.IntegerField(label=label, choices=list(range(0, 11)))


def belief_pct_field(label):
    return models.IntegerField(label=label, min=0, max=100)


class Player(BasePlayer):
    # randomization record
    error_order = models.StringField()

    # Quantitative Analysis = Optimization task (Weidmann & Deming), 3 rounds.
    # Per round: function used, guesses as JSON [[x, f(x)], ...] (recorded by the
    # server), final answer, its value, and score in [0, 1].
    opt_practice_guesses = models.LongStringField(blank=True)
    opt1_function = models.StringField(blank=True)
    opt2_function = models.StringField(blank=True)
    opt3_function = models.StringField(blank=True)
    opt1_guesses = models.LongStringField(blank=True)
    opt2_guesses = models.LongStringField(blank=True)
    opt3_guesses = models.LongStringField(blank=True)
    opt1_final = models.FloatField(blank=True)
    opt2_final = models.FloatField(blank=True)
    opt3_final = models.FloatField(blank=True)
    opt1_final_value = models.FloatField(blank=True)
    opt2_final_value = models.FloatField(blank=True)
    opt3_final_value = models.FloatField(blank=True)
    opt1_score = models.FloatField(blank=True)
    opt2_score = models.FloatField(blank=True)
    opt3_score = models.FloatField(blank=True)
    opt1_focus_lost = models.IntegerField(blank=True)
    opt2_focus_lost = models.IntegerField(blank=True)
    opt3_focus_lost = models.IntegerField(blank=True)
    opt1_copy_paste = models.IntegerField(blank=True)
    opt2_copy_paste = models.IntegerField(blank=True)
    opt3_copy_paste = models.IntegerField(blank=True)
    # mean score over the 3 rounds (0-1), as in Weidmann & Deming
    quant_score = models.FloatField(blank=True)

    # Quant beliefs
    quant_belief_score = models.IntegerField(
        label='On average, how close do you think your final answers came to the highest possible value?',
        min=0, max=100,
    )
    quant_belief_pct = belief_pct_field(
        'What percentage of participants working on the <strong>Quantitative Analysis</strong> task do you think you outperformed?'
    )

    # Error Detection Task (text entry, not forced)
    err_q52 = models.StringField(blank=True)
    err_q62 = models.StringField(blank=True)
    err_q63 = models.StringField(blank=True)
    err_q64 = models.StringField(blank=True)
    err_q65 = models.StringField(blank=True)
    err_q66 = models.StringField(blank=True)
    err_q67 = models.StringField(blank=True)
    err_q68 = models.StringField(blank=True)
    err_q69 = models.StringField(blank=True)
    err_q70 = models.StringField(blank=True)
    error_score = models.IntegerField()

    # Error beliefs (QID46, QID47)
    error_belief_correct = belief_correct_field(
        'Out of the 10 questions on the <strong>Error Detection</strong> task, how many questions do you think you answered correctly?'
    )
    error_belief_pct = belief_pct_field(
        'What percentage of participants working on the <strong>Error Detection</strong> task do you think you outperformed?'
    )

    # Research Communication Task (QID76, QID95)
    comm_headline = models.LongStringField(blank=True)
    comm_summary = models.LongStringField(blank=True)

    # Anti-cheating traces on the task pages (see _static/global/js/anticheat.js):
    # times the study window lost focus, and blocked copy/paste attempts
    quant_focus_lost = models.IntegerField(blank=True)
    quant_copy_paste = models.IntegerField(blank=True)
    error_focus_lost = models.IntegerField(blank=True)
    error_copy_paste = models.IntegerField(blank=True)
    comm_focus_lost = models.IntegerField(blank=True)
    comm_copy_paste = models.IntegerField(blank=True)

    # Attention check 2 (instructed response: correct answer = 2 'Somewhat disagree')
    attention_check_2 = models.IntegerField(
        choices=[
            [1, 'Strongly disagree'],
            [2, 'Somewhat disagree'],
            [3, 'Neither agree nor disagree'],
            [4, 'Somewhat agree'],
            [5, 'Strongly agree'],
        ],
        widget=widgets.RadioSelect,
    )
    attention_check_2_passed = models.BooleanField()

    # Communication beliefs (QID79, QID80)
    comm_belief_correct = belief_correct_field(
        'Out of the 10 readers who will evaluate your response on the&nbsp;<strong>Research Communication</strong>&nbsp;task,  how many do you think will correctly identify the article’s main finding based on what you wrote?'
    )
    comm_belief_pct = belief_pct_field(
        'What percentage of participants working on the <strong>Research Communication</strong>&nbsp;task do you think you outperformed?'
    )


# ---------- helpers ----------
def _parse_int(s):
    try:
        return int(str(s).strip())
    except (TypeError, ValueError):
        return None


# ---------- PAGES ----------
class Stage1Instructions(Page):
    pass


class QuantInstructions(Page):
    """Instructions + practice (their 'individual' intro)."""

    form_model = 'player'

    @staticmethod
    def vars_for_template(player):
        return dict(
            curve=json.dumps(opt.practice_curve()),
            practice=True,
            max_guesses=opt.MAX_GUESSES,
            rounds=len(opt.ROUND_FUNCTIONS),
        )

    @staticmethod
    def live_method(player, data):
        return opt_live_practice(player, data)

    @staticmethod
    def error_message(player, values):
        if not player.field_maybe_none('opt_practice_guesses'):
            return 'Enter a number between 0 and 300 before continuing!'


def opt_live_practice(player, data):
    """Practice guesses on the example function (not scored)."""
    try:
        x = float(data.get('guess'))
    except (TypeError, ValueError):
        return {player.id_in_group: dict(type='error')}
    if not (opt.X_MIN <= x <= opt.X_MAX):
        return {player.id_in_group: dict(type='error')}
    guesses = json.loads(player.field_maybe_none('opt_practice_guesses') or '[]')
    y = opt.value(opt.PRACTICE_FUNCTION, x)
    guesses.append([x, y])
    player.opt_practice_guesses = json.dumps(guesses)
    return {player.id_in_group: dict(type='result', guess=x, result=y, n=len(guesses))}


class OptRound(Page):
    """One scored round of the Optimization task (template OptRound.html)."""

    form_model = 'player'
    template_name = 'screening/OptRound.html'
    round = 1

    @classmethod
    def get_form_fields(cls, player):
        return [f'opt{cls.round}_focus_lost', f'opt{cls.round}_copy_paste']

    @classmethod
    def _fn(cls, player):
        fn = player.field_maybe_none(f'opt{cls.round}_function')
        if not fn:
            fn = opt.ROUND_FUNCTIONS[cls.round - 1]
            setattr(player, f'opt{cls.round}_function', fn)
        return fn

    @classmethod
    def vars_for_template(cls, player):
        cls._fn(player)
        guesses = json.loads(player.field_maybe_none(f'opt{cls.round}_guesses') or '[]')
        return dict(
            round=cls.round,
            max_guesses=opt.MAX_GUESSES,
            practice=False,
            prior=json.dumps(guesses),
            has_final=player.field_maybe_none(f'opt{cls.round}_final') is not None,
        )

    @classmethod
    def live_method(cls, player, data):
        r = cls.round
        fn = cls._fn(player)
        pid = player.id_in_group
        guesses = json.loads(player.field_maybe_none(f'opt{r}_guesses') or '[]')
        if player.field_maybe_none(f'opt{r}_final') is not None:
            return {pid: dict(type='done')}
        try:
            x = float(data.get('guess'))
        except (TypeError, ValueError):
            return {pid: dict(type='error')}
        if not (opt.X_MIN <= x <= opt.X_MAX):
            return {pid: dict(type='error')}
        if data.get('type') == 'guess' and len(guesses) < opt.MAX_GUESSES:
            y = opt.value(fn, x)
            guesses.append([x, y])
            setattr(player, f'opt{r}_guesses', json.dumps(guesses))
            return {pid: dict(type='result', guess=x, result=y, n=len(guesses))}
        if data.get('type') == 'final' and len(guesses) >= opt.MAX_GUESSES:
            setattr(player, f'opt{r}_final', x)
            return {pid: dict(type='final_saved')}
        return {pid: dict(type='error')}

    @classmethod
    def error_message(cls, player, values):
        if player.field_maybe_none(f'opt{cls.round}_final') is None:
            return 'Please make all your guesses and enter your final answer.'

    @classmethod
    def before_next_page(cls, player, timeout_happened):
        r = cls.round
        fn = cls._fn(player)
        final = player.field_maybe_none(f'opt{r}_final')
        if final is not None:
            setattr(player, f'opt{r}_final_value', opt.value(fn, final))
            setattr(player, f'opt{r}_score', round(opt.score(fn, final), 4))
        if r == 3:
            scores = [player.field_maybe_none(f'opt{i}_score') for i in (1, 2, 3)]
            player.quant_score = round(sum(s or 0 for s in scores) / 3, 4)
            player.quant_focus_lost = sum(player.field_maybe_none(f'opt{i}_focus_lost') or 0 for i in (1, 2, 3))
            player.quant_copy_paste = sum(player.field_maybe_none(f'opt{i}_copy_paste') or 0 for i in (1, 2, 3))


class OptRound1(OptRound):
    round = 1


class OptRound2(OptRound):
    round = 2


class OptRound3(OptRound):
    round = 3


class OptAgain2(Page):
    template_name = 'screening/OptAgain.html'

    @staticmethod
    def vars_for_template(player):
        return dict(round=2)


class OptAgain3(Page):
    template_name = 'screening/OptAgain.html'

    @staticmethod
    def vars_for_template(player):
        return dict(round=3)


class BeliefsPage(Page):
    """Qualtrics blocks 'Quant/Error Detection/Communication Beliefs'."""

    form_model = 'player'
    template_name = 'screening/Beliefs.html'


class QuantBeliefs(BeliefsPage):
    form_fields = ['quant_belief_score', 'quant_belief_pct']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            f_correct='quant_belief_score',
            f_pct='quant_belief_pct',
            task='Quantitative Analysis',
            reader=False,
            optimization=True,
        )


class ErrorInstructions(Page):
    pass


class ErrorTask(Page):
    form_model = 'player'
    form_fields = [t['key'] for t in ERROR_TABLES] + ['error_focus_lost', 'error_copy_paste']
    timeout_seconds = C.ERROR_SECONDS

    @staticmethod
    def vars_for_template(player: Player):
        by_key = {t['key']: t for t in ERROR_TABLES}
        tables = [
            dict(key=k, rows=[list(r) for r in by_key[k]['rows']])
            for k in player.error_order.split(',')
        ]
        return dict(tables=tables)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.error_score = sum(
            1 for t in ERROR_TABLES if _parse_int(player.field_maybe_none(t['key'])) == t['correct']
        )


class ErrorBeliefs(BeliefsPage):
    form_fields = ['error_belief_correct', 'error_belief_pct']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            f_correct='error_belief_correct',
            f_pct='error_belief_pct',
            task='Error Detection',
            reader=False,
            optimization=False,
        )


class CommInstructions(Page):
    pass


class CommTask(Page):
    form_model = 'player'
    form_fields = ['comm_headline', 'comm_summary', 'comm_focus_lost', 'comm_copy_paste']
    timeout_seconds = C.COMM_SECONDS


class CommBeliefs(BeliefsPage):
    form_fields = ['comm_belief_correct', 'comm_belief_pct']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            f_correct='comm_belief_correct',
            f_pct='comm_belief_pct',
            task='Research Communication',
            reader=True,
            optimization=False,
        )


class AttentionCheck2(Page):
    form_model = 'player'
    form_fields = ['attention_check_2']

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if walkthrough.is_on(player):
            return
        player.attention_check_2_passed = player.attention_check_2 == 2
        if not player.attention_check_2_passed:
            player.participant.attention_fails += 1


class AttentionFailed(Page):
    """Screen-out once the participant has failed too many attention checks."""

    template_name = 'global/AttentionFailed.html'
    screen_out = True

    @staticmethod
    def is_displayed(player: Player):
        return player.participant.attention_fails >= player.session.config['attention_fails_to_exclude']


class EndStage1(Page):
    pass


page_sequence = [
    Stage1Instructions,
    QuantInstructions,
    OptRound1,
    OptAgain2,
    OptRound2,
    OptAgain3,
    OptRound3,
    QuantBeliefs,
    ErrorInstructions,
    ErrorTask,
    ErrorBeliefs,
    CommInstructions,
    CommTask,
    CommBeliefs,
    AttentionCheck2,
    AttentionFailed,
    EndStage1,
]

walkthrough.apply(page_sequence)
