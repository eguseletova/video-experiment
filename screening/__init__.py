from otree.api import *
import walkthrough
import random

doc = """
Stage 1: Screening (Qualtrics group "Screening Tasks").
Quantitative Analysis (3 min) -> beliefs, Error Detection (2 min) -> beliefs,
Research Communication (3 min) -> beliefs, End of Stage 1.
Question order within each task is randomized (Qualtrics "RandomizeAll"),
and quant answer options are shuffled (Qualtrics choice randomization).
"""

IMG = '/static/global/img/'

# Qualtrics QID14, 18-26 (export tags Task_Q1..Task_Q10).
# 'correct' is the choice code of the right answer (not in Qualtrics; added for scoring).
QUANT_QUESTIONS = [
    dict(
        key='task_q1',
        text='A number is increased by 20%, then decreased by 20%. What is the overall change?',
        choices=[[1, 'No change'], [2, '4% decrease'], [3, '4% increase'], [4, '10% decrease']],
        correct=2,
    ),
    dict(
        key='task_q2',
        text='A researcher tests whether there is a difference between two groups and obtains a result of p = .43. What can they conclude?',
        choices=[
            [1, 'The result is statistically significant at the 5% level'],
            [2, 'The two groups are identical'],
            [3, 'There is insufficient evidence of a difference'],
            [4, 'The study should be repeated'],
        ],
        correct=3,
    ),
    dict(
        key='task_q3',
        text='A dataset has the following values: 3, 4, 4, 5, 34. Which statement is true?',
        choices=[
            [1, 'The mean accurately represents the typical value'],
            [2, 'The mean is pulled up by the largest value'],
            [3, 'The mean and median are equal'],
            [4, 'The largest value has no effect on the mean'],
        ],
        correct=2,
    ),
    dict(
        key='task_q4',
        text=(
            'The scatter plot below shows hours studied and exam scores for 8 students. '
            'Which statement best describes the relationship?<br>'
            f'<img src="{IMG}scatter.png" style="width:700px; max-width:100%; height:auto;" alt="Scatter plot of hours studied vs exam score"><br>'
        ),
        choices=[
            [1, 'No relationship'],
            [2, 'Positive relationship'],
            [3, 'Negative relationship'],
            [4, 'Curvilinear relationship'],
        ],
        correct=2,
    ),
    dict(
        key='task_q5',
        text=(
            'Two groups each take a test. Group A (n=50) has an average score of 70. '
            'Group B (n=100) has an average score of 70. A colleague concludes the groups '
            'performed identically. What is the main problem with this conclusion?'
        ),
        choices=[
            [1, 'The means were calculated incorrectly'],
            [2, 'You cannot compare groups with different sample sizes'],
            [3, 'Equal averages do not mean the scores were distributed the same way'],
            [4, 'There is no problem - the conclusion is correct'],
        ],
        correct=3,
    ),
    dict(
        key='task_q6',
        text=(
            '<p>The table below shows how many participants in two groups responded '
            '&ldquo;Yes&rdquo; or &ldquo;No&rdquo; to a survey question.</p>'
            '<table class="yn-table"><tbody>'
            '<tr><td>&nbsp;</td><td>Yes</td><td>No</td></tr>'
            '<tr><td>Group A</td><td>30</td><td>70</td></tr>'
            '<tr><td>Group B</td><td>20</td><td>30</td></tr>'
            '</tbody></table>'
            '<p>Which group had a higher rate of &ldquo;Yes&rdquo; responses?</p>'
        ),
        choices=[
            [1, 'Group A'],
            [2, 'Group B'],
            [3, 'Both groups had the same "Yes" rate'],
            [4, 'Cannot be determined from the table'],
        ],
        correct=2,
    ),
    dict(
        key='task_q7',
        text=(
            'A research team surveyed 60 participants. 30 participants read Article A. '
            '25 participants read Article B. 10 participants read both articles. '
            'How many participants read neither article?'
        ),
        choices=[[1, '5'], [2, '15'], [3, '20'], [4, '25']],
        correct=2,
    ),
    dict(
        key='task_q8',
        text='If x*x = 289, what 2 values could x have?',
        choices=[[1, '-17 & 17'], [2, '-16 & 16'], [3, '-18 & 18'], [4, '-19 & 19']],
        correct=1,
    ),
    dict(
        key='task_q9',
        text=(
            'The sum of the digits of a certain two-digit number is 7. '
            'Reversing its digits increases the number by 9. What is the number?'
        ),
        choices=[[1, '25'], [2, '52'], [3, '16'], [4, '34']],
        correct=4,
    ),
    dict(
        key='task_q10',
        text=(
            'Version A of a survey was completed by 30 out of 50 participants. '
            'Version B was completed by 50 out of 100 participants. '
            'Which version had a higher completion rate?'
        ),
        choices=[[1, 'Version A'], [2, 'Version B'], [3, 'They were equal'], [4, 'Cannot be determined']],
        correct=1,
    ),
]

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
    QUANT_SECONDS = 180
    ERROR_SECONDS = 120
    COMM_SECONDS = 180


class Subsession(BaseSubsession):
    pass


def creating_session(subsession: Subsession):
    for p in subsession.get_players():
        q_order = list(range(len(QUANT_QUESTIONS)))
        random.shuffle(q_order)
        p.quant_order = ','.join(QUANT_QUESTIONS[i]['key'] for i in q_order)
        e_order = list(range(len(ERROR_TABLES)))
        random.shuffle(e_order)
        p.error_order = ','.join(ERROR_TABLES[i]['key'] for i in e_order)
        # per-question choice order for the quant task
        p.quant_choice_order = ';'.join(
            q['key'] + ':' + ','.join(str(c[0]) for c in random.sample(q['choices'], len(q['choices'])))
            for q in QUANT_QUESTIONS
        )


class Group(BaseGroup):
    pass


def belief_correct_field(label):
    return models.IntegerField(label=label, choices=list(range(0, 11)))


def belief_pct_field(label):
    return models.IntegerField(label=label, min=0, max=100)


class Player(BasePlayer):
    # randomization record
    quant_order = models.StringField()
    quant_choice_order = models.StringField()
    error_order = models.StringField()

    # Quantitative Analysis Task (not forced)
    task_q1 = models.IntegerField(blank=True)
    task_q2 = models.IntegerField(blank=True)
    task_q3 = models.IntegerField(blank=True)
    task_q4 = models.IntegerField(blank=True)
    task_q5 = models.IntegerField(blank=True)
    task_q6 = models.IntegerField(blank=True)
    task_q7 = models.IntegerField(blank=True)
    task_q8 = models.IntegerField(blank=True)
    task_q9 = models.IntegerField(blank=True)
    task_q10 = models.IntegerField(blank=True)
    quant_score = models.IntegerField()

    # Quant beliefs (QID34, QID35)
    quant_belief_correct = belief_correct_field(
        'Out of the 10 questions on the <strong>Quantitative Analysis</strong> task, how many questions do you think you answered correctly?'
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
    pass


class QuantTask(Page):
    form_model = 'player'
    form_fields = [q['key'] for q in QUANT_QUESTIONS] + ['quant_focus_lost', 'quant_copy_paste']
    timeout_seconds = C.QUANT_SECONDS

    @staticmethod
    def vars_for_template(player: Player):
        by_key = {q['key']: q for q in QUANT_QUESTIONS}
        choice_order = dict(
            item.split(':') for item in player.quant_choice_order.split(';')
        )
        questions = []
        for key in player.quant_order.split(','):
            q = by_key[key]
            labels = dict(q['choices'])
            order = [int(c) for c in choice_order[key].split(',')]
            questions.append(
                dict(key=key, text=q['text'], choices=[(c, labels[c]) for c in order])
            )
        return dict(questions=questions)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.quant_score = sum(
            1 for q in QUANT_QUESTIONS if player.field_maybe_none(q['key']) == q['correct']
        )


class BeliefsPage(Page):
    """Qualtrics blocks 'Quant/Error Detection/Communication Beliefs'."""

    form_model = 'player'
    template_name = 'screening/Beliefs.html'


class QuantBeliefs(BeliefsPage):
    form_fields = ['quant_belief_correct', 'quant_belief_pct']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            f_correct='quant_belief_correct',
            f_pct='quant_belief_pct',
            task='Quantitative Analysis',
            reader=False,
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
    QuantTask,
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
