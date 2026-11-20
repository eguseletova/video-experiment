from otree.api import *
import walkthrough
import video_upload

doc = """
Stage 2: Resume + three video introductions (A, B, C), each answering a
different prompt, recorded with automatic background blur (max 1 minute,
max 2 re-recordings each). After all three videos: hiring likelihood per
video, then a ranking of the three videos. Then the participant chooses ONE
video to send (video_sent),
followed by a multiple price list (MPL) eliciting willingness to pay to send
an ADDITIONAL video.

Video is purely cosmetic for now: recordings never leave the participant's
browser (kept in the browser's IndexedDB only so they can be replayed on the
choice page). Nothing is uploaded to the oTree server.
"""


class C(BaseConstants):
    NAME_IN_URL = 'stage2'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    VIDEO_MAX_SECONDS = 60
    VIDEO_MAX_TAKES = 3  # 1 original recording + 2 re-recordings
    # Video prompts per study version (session config 'prompt_set')
    PROMPT_SETS = {
        'cv': {
            'a': 'Tell the recruiter about one of the skills presented in your CV.',
            'b': 'Tell the recruiter something they would not be able to tell from your CV.',
            'c': 'Tell the recruiter why you would be a good fit for this role.',
        },
        'goals': {
            'a': 'Your goal is to appear competent.',
            'b': 'Your goal is to appear likeable.',
            'c': 'Your goal is to be hired.',
        },
    }
    # MPL: price (USD) of sending one additional video, one row per price
    MPL_PRICES = [0.00, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00]
    # Comprehension check: (field, question, choices, correct)
    COMPREHENSION = [
        ('comp_1', 'How many videos will you record?',
         [[1, '1'], [2, '2'], [3, '3'], [4, '4']], 3),
        ('comp_2', 'What is the maximum length of each video?',
         [[1, '30 seconds'], [2, '1 minute'], [3, '2 minutes'], [4, '5 minutes']], 2),
        ('comp_3', 'How many times can you re-record each video?',
         [[1, 'Not at all'], [2, 'Once'], [3, 'Up to 2 times'], [4, 'As many times as I like']], 3),
        ('comp_4', 'Which of the following should you NOT include in your videos?',
         [[1, 'Information about your skills'],
          [2, 'Your full name, contact information, or age'],
          [3, 'Why you would be a good fit for the role']], 2),
    ]


class Subsession(BaseSubsession):
    pass


def creating_session(subsession: Subsession):
    for p in subsession.get_players():
        p.prompt_set = subsession.session.config.get('prompt_set', 'cv')


class Group(BaseGroup):
    pass


def hire_belief_field(letter):
    return models.IntegerField(
        label=f'How likely do you think you will be hired if the recruiter only saw Video {letter.upper()}?',
        min=0,
        max=100,
    )


def comp_field(i):
    _, q, choices, _ = C.COMPREHENSION[i]
    return models.IntegerField(label=q, choices=choices, widget=widgets.RadioSelect)


def mpl_field(price):
    return models.IntegerField(
        label=f'${price:.2f}',
        choices=[[1, f'Pay ${price:.2f} and send an additional video'], [0, 'Do not send an additional video']],
    )


def rank_field(letter):
    return models.IntegerField(
        label=f'Rank of Video {letter.upper()} (1 = most likely to get you hired)',
        choices=[1, 2, 3],
    )


class Player(BasePlayer):
    prompt_set = models.StringField(doc="Video prompt version: 'cv' or 'goals'")

    # Comprehension check
    comp_1 = comp_field(0)
    comp_2 = comp_field(1)
    comp_3 = comp_field(2)
    comp_4 = comp_field(3)
    comp_failed_attempts = models.IntegerField(initial=0)

    # Name or alias used in the videos
    video_name = models.StringField(
        label='Please enter the name or alias you would like to use in your videos.'
    )

    # Per video: recording made? length of final take (s), number of takes
    video_a_recorded = models.BooleanField(blank=True)
    video_b_recorded = models.BooleanField(blank=True)
    video_c_recorded = models.BooleanField(blank=True)
    video_a_seconds = models.FloatField(blank=True)
    video_b_seconds = models.FloatField(blank=True)
    video_c_seconds = models.FloatField(blank=True)
    video_a_takes = models.IntegerField(blank=True)
    video_b_takes = models.IntegerField(blank=True)
    video_c_takes = models.IntegerField(blank=True)
    # Set by the server once the final take reached the oTree server (it is then
    # forwarded to Box in the background; see video_upload.py), and the file name
    video_a_uploaded = models.BooleanField(blank=True)
    video_b_uploaded = models.BooleanField(blank=True)
    video_c_uploaded = models.BooleanField(blank=True)
    video_a_file = models.StringField(blank=True)
    video_b_file = models.StringField(blank=True)
    video_c_file = models.StringField(blank=True)

    # Beliefs after all three videos: hiring likelihood per video (0-100 %) ...
    hire_belief_a = hire_belief_field('a')
    hire_belief_b = hire_belief_field('b')
    hire_belief_c = hire_belief_field('c')
    # ... and ranking if the recruiter only saw one video (1 = most likely hired)
    rank_a = rank_field('a')
    rank_b = rank_field('b')
    rank_c = rank_field('c')

    # Which single video the participant chose to send
    video_sent = models.StringField(choices=[['a', 'Video A'], ['b', 'Video B'], ['c', 'Video C']])

    # MPL: willingness to pay to send an ADDITIONAL video (1 = pay & send, 0 = don't)
    mpl_1 = mpl_field(C.MPL_PRICES[0])
    mpl_2 = mpl_field(C.MPL_PRICES[1])
    mpl_3 = mpl_field(C.MPL_PRICES[2])
    mpl_4 = mpl_field(C.MPL_PRICES[3])
    mpl_5 = mpl_field(C.MPL_PRICES[4])
    mpl_6 = mpl_field(C.MPL_PRICES[5])
    mpl_7 = mpl_field(C.MPL_PRICES[6])
    mpl_8 = mpl_field(C.MPL_PRICES[7])
    mpl_9 = mpl_field(C.MPL_PRICES[8])
    mpl_10 = mpl_field(C.MPL_PRICES[9])
    mpl_11 = mpl_field(C.MPL_PRICES[10])
    mpl_max_wtp = models.FloatField(
        doc='Highest price at which the participant chose to pay (None if never).', blank=True
    )
    mpl_extra_video = models.StringField(
        label='If you send an additional video, which one would you send?',
        widget=widgets.RadioSelect,
    )


LETTERS = ['a', 'b', 'c']
MPL_FIELDS = [f'mpl_{i + 1}' for i in range(len(C.MPL_PRICES))]
COMP_FIELDS = [c[0] for c in C.COMPREHENSION]


def mpl_extra_video_choices(player: Player):
    return [[l, f'Video {l.upper()}'] for l in LETTERS if l != player.field_maybe_none('video_sent')]


def prompts(player):
    return C.PROMPT_SETS[player.session.config.get('prompt_set', 'cv')]


def video_list(player):
    pr = prompts(player)
    return [dict(letter=l, upper=l.upper(), prompt=pr[l], n=i + 1) for i, l in enumerate(LETTERS)]


def length_text(seconds):
    if seconds % 60:
        return f'{seconds} seconds'
    m = seconds // 60
    return '1 minute' if m == 1 else f'{m} minutes'


# ---------- PAGES ----------
class JobPosting(Page):
    pass


class ResumeInfo(Page):
    pass


class VideoInstructions(Page):
    pass


class Comprehension(Page):
    form_model = 'player'
    form_fields = COMP_FIELDS

    @staticmethod
    def vars_for_template(player: Player):
        return dict(questions=[dict(field=c[0], text=c[1]) for c in C.COMPREHENSION])

    @staticmethod
    def error_message(player: Player, values):
        wrong = [f for f, _, _, correct in C.COMPREHENSION if values[f] != correct]
        if wrong:
            player.comp_failed_attempts += 1
            return (
                f'{len(wrong)} of your answers {"is" if len(wrong) == 1 else "are"} incorrect. '
                'Please review the instructions (click "Review the instructions" above) and try again.'
            )


class VideoName(Page):
    form_model = 'player'
    form_fields = ['video_name']


class VideoPage(Page):
    form_model = 'player'
    template_name = 'stage2/VideoRecord.html'
    letter = 'a'

    @classmethod
    def get_form_fields(cls, player):
        l = cls.letter
        return [f'video_{l}_recorded', f'video_{l}_seconds', f'video_{l}_takes']

    @classmethod
    def vars_for_template(cls, player):
        return dict(
            letter=cls.letter,
            upper=cls.letter.upper(),
            number=LETTERS.index(cls.letter) + 1,
            prompt=prompts(player)[cls.letter],
            max_seconds=C.VIDEO_MAX_SECONDS,
            max_length=length_text(C.VIDEO_MAX_SECONDS),
            max_takes=C.VIDEO_MAX_TAKES,
            max_rerecords=C.VIDEO_MAX_TAKES - 1,
            video_name=player.field_maybe_none('video_name') or '',
            upload=bool(player.session.config.get('video_upload', True)),
        )

    @staticmethod
    def live_method(player, data):
        return video_upload.live_method(player, data)


class VideoA(VideoPage):
    letter = 'a'


class VideoB(VideoPage):
    letter = 'b'


class VideoC(VideoPage):
    letter = 'c'


class HireBeliefs(Page):
    """After all three videos: hiring likelihood if the recruiter only saw that video."""

    form_model = 'player'
    form_fields = ['hire_belief_a', 'hire_belief_b', 'hire_belief_c']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(videos=video_list(player))


class HireRanking(Page):
    """Rank the three videos (if the recruiter only saw one)."""

    form_model = 'player'
    form_fields = ['rank_a', 'rank_b', 'rank_c']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(videos=video_list(player))

    @staticmethod
    def error_message(player: Player, values):
        if sorted(values[f] for f in ['rank_a', 'rank_b', 'rank_c']) != [1, 2, 3]:
            return 'Please give each video a different rank (1, 2 and 3).'


class ChooseVideo(Page):
    form_model = 'player'
    form_fields = ['video_sent']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(videos=video_list(player))


class AdditionalVideoMPL(Page):
    form_model = 'player'
    form_fields = MPL_FIELDS + ['mpl_extra_video']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            rows=[
                dict(field=f, price=f'${p:.2f}', i=i + 1)
                for i, (f, p) in enumerate(zip(MPL_FIELDS, C.MPL_PRICES))
            ],
            sent_upper=(player.field_maybe_none('video_sent') or 'a').upper(),
        )

    @staticmethod
    def error_message(player: Player, values):
        choices = [values[f] for f in MPL_FIELDS]
        # single switching point: once "do not send" is chosen, all higher prices must be "do not send"
        if any(choices[i] == 0 and choices[i + 1] == 1 for i in range(len(choices) - 1)):
            return (
                'Please choose consistently: if you would not pay a given price, '
                'you should not pay any higher price either.'
            )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        paid = [p for f, p in zip(MPL_FIELDS, C.MPL_PRICES) if getattr(player, f) == 1]
        player.mpl_max_wtp = max(paid) if paid else None


page_sequence = [
    JobPosting,
    ResumeInfo,
    VideoInstructions,
    Comprehension,
    VideoName,
    VideoA,
    VideoB,
    VideoC,
    HireBeliefs,
    HireRanking,
    ChooseVideo,
    AdditionalVideoMPL,
]

walkthrough.apply(page_sequence)
