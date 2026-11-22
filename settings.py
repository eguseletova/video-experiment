from os import environ
from pathlib import Path

# Study-identifying details (consent form contacts, IRB number, Prolific code)
# are NOT stored in this repository. Put them in a local file `study.env`
# (KEY=VALUE lines, git-ignored) or set them as environment variables on the
# server. Missing values show as placeholders.
_env_file = Path(__file__).resolve().parent / 'study.env'
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        if '=' in _line and not _line.strip().startswith('#'):
            _k, _v = _line.split('=', 1)
            environ.setdefault(_k.strip(), _v.strip())

STUDY = dict(
    completion_url=environ.get('PROLIFIC_COMPLETION_URL', 'https://app.prolific.com/'),
    consent_institutions=environ.get('CONSENT_INSTITUTIONS', '[university names]'),
    consent_study_id=environ.get('CONSENT_STUDY_ID', '[IRB study number]'),
    consent_sponsor=environ.get('CONSENT_SPONSOR', '[sponsor]'),
    consent_disclosing_institution=environ.get('CONSENT_DISCLOSING_INSTITUTION', '[university]'),
    consent_contact_name=environ.get('CONSENT_CONTACT_NAME', '[researcher name]'),
    consent_contact_email=environ.get('CONSENT_CONTACT_EMAIL', '[researcher email]'),
    consent_irb_contact=environ.get('CONSENT_IRB_CONTACT', '[IRB office, email and phone]'),
)

APPS = ['intro', 'screening', 'stage2', 'post']

COMMON = dict(
    app_sequence=APPS,
    # Prolific completion redirect and consent-form details (see STUDY above)
    **STUDY,
    # Developer mode: shows a bold red "CHECK" marker on pages flagged for review.
    dev_mode=True,
    # Participants are screened out once they have failed this many attention checks
    # (2 = must fail both; Prolific only allows rejections after 2 failed checks).
    attention_fails_to_exclude=2,
    # Anti-cheating: no copy/paste, screen blurs when the window loses focus, etc.
    anti_cheat=True,
    # Send each final video to the server -> Box (see video_upload.py).
    video_upload=True,
    # Walk-through mode: click through without answering (see walkthrough.py).
    walkthrough=False,
    # Video prompt set: 'cv' (CV-based prompts) or 'goals' (goal prompts); see stage2.C.PROMPT_SETS
    prompt_set='cv',
)

SESSION_CONFIGS = [
    dict(
        COMMON,
        name='video_experiment',
        display_name='Video Experiment — Version 1: CV prompts',
        num_demo_participants=1,
        prompt_set='cv',
    ),
    dict(
        COMMON,
        name='video_experiment_goals',
        display_name='Video Experiment — Version 2: goal prompts (competent / likeable / hired)',
        num_demo_participants=1,
        prompt_set='goals',
    ),
    dict(
        COMMON,
        name='video_experiment_walkthrough',
        display_name='WALK-THROUGH (no answers required) — Version 1: CV prompts',
        num_demo_participants=1,
        prompt_set='cv',
        walkthrough=True,
    ),
    dict(
        COMMON,
        name='video_experiment_goals_walkthrough',
        display_name='WALK-THROUGH (no answers required) — Version 2: goal prompts',
        num_demo_participants=1,
        prompt_set='goals',
        walkthrough=True,
    ),
]

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=3.00, doc=""
)

PARTICIPANT_FIELDS = [
    'workerid',         # Qualtrics embedded data "workerid" (random ID 10000-10322)
    'attention_fails',  # number of failed attention checks
]
SESSION_FIELDS = []

# Prolific study URL for each version:
# https://<server>/room/<room name>?participant_label={{%PROLIFIC_PID%}}
ROOMS = [
    dict(name='video_experiment', display_name='Video Experiment — Version 1 (Prolific)'),
    dict(name='video_experiment_goals', display_name='Video Experiment — Version 2 (Prolific)'),
]

LANGUAGE_CODE = 'en'
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = False

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """
oTree reproduction of the Qualtrics survey <i>Video Experiment</i>.
"""

SECRET_KEY = environ.get('OTREE_SECRET_KEY', 'local-development-only')

INSTALLED_APPS = ['otree']
