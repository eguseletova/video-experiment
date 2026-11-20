from otree.api import *
import walkthrough

doc = """
Post-task questionnaires: Demographics (Qualtrics QID96-100), then
- LSAS-SR: Liebowitz Social Anxiety Scale, self-report (24 items x fear/anxiety + avoidance)
- Neuroticism: IPIP Big-Five Factor Markers, Emotional Stability (10 items, public domain), scored as neuroticism
- RSES: Rosenberg Self-Esteem Scale (10 items)
- GAD-7: Generalized Anxiety Disorder scale (7 items + functional-impairment item)
then the exit questions (QID85, QID83) and the redirect to Prolific.
"""


class C(BaseConstants):
    NAME_IN_URL = 'post'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    # ---- LSAS-SR (Liebowitz, 1987; self-report version) ----
    # (item text, subscale: P = performance, S = social interaction)
    LSAS_ITEMS = [
        ('Telephoning in public', 'P'),
        ('Participating in small groups', 'P'),
        ('Eating in public places', 'P'),
        ('Drinking with others in public places', 'P'),
        ('Talking to people in authority', 'S'),
        ('Acting, performing or giving a talk in front of an audience', 'P'),
        ('Going to a party', 'S'),
        ('Working while being observed', 'P'),
        ('Writing while being observed', 'P'),
        ("Calling someone you don't know very well", 'S'),
        ("Talking with people you don't know very well", 'S'),
        ('Meeting strangers', 'S'),
        ('Urinating in a public bathroom', 'P'),
        ('Entering a room when others are already seated', 'P'),
        ('Being the center of attention', 'S'),
        ('Speaking up at a meeting', 'P'),
        ('Taking a test', 'P'),
        ("Expressing a disagreement or disapproval to people you don't know very well", 'S'),
        ("Looking at people you don't know very well in the eyes", 'S'),
        ('Giving a report to a group', 'P'),
        ('Trying to pick up someone', 'P'),
        ('Returning goods to a store', 'S'),
        ('Giving a party', 'S'),
        ('Resisting a high pressure salesperson', 'S'),
    ]
    LSAS_FEAR_SCALE = [[0, 'None'], [1, 'Mild'], [2, 'Moderate'], [3, 'Severe']]
    LSAS_AVOID_SCALE = [[0, 'Never'], [1, 'Occasionally'], [2, 'Often'], [3, 'Usually']]
    LSAS_PAGES = 3  # 24 situations split over 3 pages of 8

    # ---- IPIP Emotional Stability (Goldberg, 1992), keyed for NEUROTICISM ----
    # (item, reverse-keyed for neuroticism?)
    NEURO_ITEMS = [
        ('Get stressed out easily.', False),
        ('Am relaxed most of the time.', True),
        ('Worry about things.', False),
        ('Seldom feel blue.', True),
        ('Am easily disturbed.', False),
        ('Get upset easily.', False),
        ('Change my mood a lot.', False),
        ('Have frequent mood swings.', False),
        ('Get irritated easily.', False),
        ('Often feel blue.', False),
    ]
    NEURO_SCALE = [
        [1, 'Very inaccurate'],
        [2, 'Moderately inaccurate'],
        [3, 'Neither accurate nor inaccurate'],
        [4, 'Moderately accurate'],
        [5, 'Very accurate'],
    ]

    # ---- Rosenberg Self-Esteem Scale (Rosenberg, 1965) ----
    RSES_ITEMS = [
        ('On the whole, I am satisfied with myself.', False),
        ('At times I think I am no good at all.', True),
        ('I feel that I have a number of good qualities.', False),
        ('I am able to do things as well as most other people.', False),
        ('I feel I do not have much to be proud of.', True),
        ('I certainly feel useless at times.', True),
        ("I feel that I'm a person of worth, at least on an equal plane with others.", False),
        ('I wish I could have more respect for myself.', True),
        ('All in all, I am inclined to feel that I am a failure.', True),
        ('I take a positive attitude toward myself.', False),
    ]
    # stored as 1-4; scored 0-3 (SA=3 ... SD=0 for positive items, reversed for negative items)
    RSES_SCALE = [[4, 'Strongly agree'], [3, 'Agree'], [2, 'Disagree'], [1, 'Strongly disagree']]

    # ---- GAD-7 (Spitzer et al., 2006) ----
    GAD_ITEMS = [
        'Feeling nervous, anxious, or on edge',
        'Not being able to stop or control worrying',
        'Worrying too much about different things',
        'Trouble relaxing',
        "Being so restless that it's hard to sit still",
        'Becoming easily annoyed or irritable',
        'Feeling afraid as if something awful might happen',
    ]
    GAD_SCALE = [[0, 'Not at all'], [1, 'Several days'], [2, 'More than half the days'], [3, 'Nearly every day']]
    GAD_DIFFICULTY = [
        [1, 'Not difficult at all'],
        [2, 'Somewhat difficult'],
        [3, 'Very difficult'],
        [4, 'Extremely difficult'],
    ]


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


def race_field(label):
    return models.BooleanField(label=label, blank=True, widget=widgets.CheckboxInput)


def _f(label, choices):
    return models.IntegerField(label=label, choices=choices, widget=widgets.RadioSelect)


class Player(BasePlayer):
    # ---------------- Demographics (QID96-100) ----------------
    age = models.StringField(label='What is your age?', blank=True)
    education = models.IntegerField(
        label='What is the highest level of school you have completed or the highest degree you have received?',
        choices=[
            [1, 'Less than high school degree'],
            [2, 'High school graduate (high school diploma or equivalent including GED)'],
            [3, 'Some college but no degree'],
            [4, 'Associate degree in college (2-year)'],
            [5, "Bachelor's degree in college (4-year)"],
            [6, "Master's degree"],
            [7, 'Doctoral degree'],
            [8, 'Professional degree (JD, MD)'],
            [9, 'Prefer not to say'],
        ],
        widget=widgets.RadioSelect,
    )
    gender = models.IntegerField(
        label='What is your gender?',
        choices=[
            [1, 'Male'],
            [2, 'Female'],
            [3, 'Non-binary'],
            [4, 'Prefer to self-describe:'],
            [5, 'Prefer not to say'],
        ],
        widget=widgets.RadioSelect,
    )
    gender_text = models.StringField(blank=True)
    shl = models.IntegerField(
        label='Are you of Hispanic, Latino/a, or Spanish origin?',
        choices=[[1, 'Yes'], [2, 'No'], [3, 'Prefer not to say']],
        widget=widgets.RadioSelect,
    )
    race_1 = race_field('American Indian or Alaskan Native')
    race_2 = race_field('Asian')
    race_3 = race_field('Black or African American')
    race_4 = race_field('Native Hawaiian or Other Pacific Islander')
    race_5 = race_field('White')
    race_6 = race_field('Other (please specify):')
    race_6_text = models.StringField(blank=True)
    race_7 = race_field('Prefer not to say')

    # ---------------- LSAS-SR ----------------
    for _i, (_txt, _sub) in enumerate(C.LSAS_ITEMS, start=1):
        locals()[f'lsas_fear_{_i}'] = _f(f'{_txt} — fear or anxiety', C.LSAS_FEAR_SCALE)
        locals()[f'lsas_avoid_{_i}'] = _f(f'{_txt} — avoidance', C.LSAS_AVOID_SCALE)
    lsas_fear_total = models.IntegerField()
    lsas_avoid_total = models.IntegerField()
    lsas_performance_total = models.IntegerField()
    lsas_social_total = models.IntegerField()
    lsas_total = models.IntegerField()

    # ---------------- Neuroticism (IPIP) ----------------
    for _i, (_txt, _rev) in enumerate(C.NEURO_ITEMS, start=1):
        locals()[f'neuro_{_i}'] = _f(_txt, C.NEURO_SCALE)
    neuro_total = models.IntegerField(doc='Sum of 10 items keyed for neuroticism (10-50).')

    # ---------------- Rosenberg Self-Esteem ----------------
    for _i, (_txt, _rev) in enumerate(C.RSES_ITEMS, start=1):
        locals()[f'rses_{_i}'] = _f(_txt, C.RSES_SCALE)
    rses_total = models.IntegerField(doc='0-30, higher = higher self-esteem.')

    # ---------------- GAD-7 ----------------
    for _i, _txt in enumerate(C.GAD_ITEMS, start=1):
        locals()[f'gad_{_i}'] = _f(_txt, C.GAD_SCALE)
    gad_difficulty = models.IntegerField(
        label=(
            'If you checked off any problems, how difficult have these problems made it for you '
            'to do your work, take care of things at home, or get along with other people?'
        ),
        choices=C.GAD_DIFFICULTY,
        widget=widgets.RadioSelect,
        blank=True,
    )
    gad_total = models.IntegerField(doc='0-21.')

    del _i, _txt
    try:
        del _sub, _rev
    except NameError:
        pass

    # ---------------- Exit screen (QID85, QID83) ----------------
    comments = models.LongStringField(blank=True)
    video_consent = models.IntegerField(
        label=(
            'The research team will be presenting the results of this study in a variety of formats '
            'and to a variety of audiences. With your permission, we may use short excerpts from your '
            'recorded video or images (e.g., screenshots) from your recording in presenting the '
            'information to various audiences. If you agree that we may utilize your video in '
            'presentations to others, please indicate below.'
        ),
        choices=[[4, 'Yes, I agree'], [5, 'No, I do not agree']],
        widget=widgets.RadioSelect,
    )


RACE_FIELDS = ['race_1', 'race_2', 'race_3', 'race_4', 'race_5', 'race_6', 'race_7']
LSAS_FEAR = [f'lsas_fear_{i}' for i in range(1, len(C.LSAS_ITEMS) + 1)]
LSAS_AVOID = [f'lsas_avoid_{i}' for i in range(1, len(C.LSAS_ITEMS) + 1)]
NEURO_FIELDS = [f'neuro_{i}' for i in range(1, len(C.NEURO_ITEMS) + 1)]
RSES_FIELDS = [f'rses_{i}' for i in range(1, len(C.RSES_ITEMS) + 1)]
GAD_FIELDS = [f'gad_{i}' for i in range(1, len(C.GAD_ITEMS) + 1)]


def likert_rows(fields, texts):
    return [dict(field=f, text=t, n=i + 1) for i, (f, t) in enumerate(zip(fields, texts))]


# ---------- PAGES ----------
class Demographics(Page):
    form_model = 'player'
    form_fields = [
        'age', 'education', 'gender', 'gender_text', 'shl',
        *RACE_FIELDS, 'race_6_text',
    ]

    @staticmethod
    def error_message(player: Player, values):
        selected = [f for f in RACE_FIELDS if values.get(f)]
        if not selected:
            return 'Please answer this question: What is your race?'
        if values.get('race_7') and len(selected) > 1:
            return '"Prefer not to say" cannot be combined with other race options.'

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        for f in RACE_FIELDS:
            if player.field_maybe_none(f) is None:
                setattr(player, f, False)


class LSASPage(Page):
    form_model = 'player'
    template_name = 'post/LSAS.html'
    part = 1

    @classmethod
    def item_range(cls):
        per = len(C.LSAS_ITEMS) // C.LSAS_PAGES
        return range((cls.part - 1) * per, cls.part * per)

    @classmethod
    def get_form_fields(cls, player):
        return [f for i in cls.item_range() for f in (LSAS_FEAR[i], LSAS_AVOID[i])]

    @classmethod
    def vars_for_template(cls, player):
        return dict(
            items=[
                dict(n=i + 1, text=C.LSAS_ITEMS[i][0], fear=LSAS_FEAR[i], avoid=LSAS_AVOID[i])
                for i in cls.item_range()
            ],
            fear_scale=C.LSAS_FEAR_SCALE,
            avoid_scale=C.LSAS_AVOID_SCALE,
            part=cls.part,
            parts=C.LSAS_PAGES,
        )


class LSAS1(LSASPage):
    part = 1


class LSAS2(LSASPage):
    part = 2


class LSAS3(LSASPage):
    part = 3

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        fear = [getattr(player, f) for f in LSAS_FEAR]
        avoid = [getattr(player, f) for f in LSAS_AVOID]
        player.lsas_fear_total = sum(fear)
        player.lsas_avoid_total = sum(avoid)
        player.lsas_total = player.lsas_fear_total + player.lsas_avoid_total
        player.lsas_performance_total = sum(
            fear[i] + avoid[i] for i, (_, s) in enumerate(C.LSAS_ITEMS) if s == 'P'
        )
        player.lsas_social_total = sum(
            fear[i] + avoid[i] for i, (_, s) in enumerate(C.LSAS_ITEMS) if s == 'S'
        )


class LikertPage(Page):
    form_model = 'player'
    template_name = 'post/Likert.html'


class Neuroticism(LikertPage):
    form_fields = NEURO_FIELDS

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            instructions=(
                'Describe yourself as you generally are now, not as you wish to be in the future. '
                'Describe yourself as you honestly see yourself, in relation to other people you know '
                'of the same sex as you are, and roughly your same age. Indicate how accurately each '
                'statement describes you.'
            ),
            stem='',
            rows=likert_rows(NEURO_FIELDS, [t for t, _ in C.NEURO_ITEMS]),
            scale=C.NEURO_SCALE,
            gad=False,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.neuro_total = sum(
            (6 - getattr(player, f)) if rev else getattr(player, f)
            for f, (_, rev) in zip(NEURO_FIELDS, C.NEURO_ITEMS)
        )


class Rosenberg(LikertPage):
    form_fields = RSES_FIELDS

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            instructions=(
                'Below is a list of statements dealing with your general feelings about yourself. '
                'Please indicate how strongly you agree or disagree with each statement.'
            ),
            stem='',
            rows=likert_rows(RSES_FIELDS, [t for t, _ in C.RSES_ITEMS]),
            scale=C.RSES_SCALE,
            gad=False,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # stored 4=SA..1=SD -> positive items: SA=3..SD=0; negative items reversed
        player.rses_total = sum(
            (getattr(player, f) - 1) if not rev else (4 - getattr(player, f))
            for f, (_, rev) in zip(RSES_FIELDS, C.RSES_ITEMS)
        )


class GAD7(LikertPage):
    form_fields = GAD_FIELDS + ['gad_difficulty']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            instructions='Over the <strong>last 2 weeks</strong>, how often have you been bothered by the following problems?',
            stem='',
            rows=likert_rows(GAD_FIELDS, C.GAD_ITEMS),
            scale=C.GAD_SCALE,
            gad=True,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.gad_total = sum(getattr(player, f) for f in GAD_FIELDS)


class Exit(Page):
    form_model = 'player'
    form_fields = ['comments', 'video_consent']


class Redirect(Page):
    """Qualtrics End of Survey -> redirect to Prolific completion URL."""

    @staticmethod
    def vars_for_template(player: Player):
        return dict(completion_url=player.session.config['completion_url'])


page_sequence = [Demographics, LSAS1, LSAS2, LSAS3, Neuroticism, Rosenberg, GAD7, Exit, Redirect]

walkthrough.apply(page_sequence)
