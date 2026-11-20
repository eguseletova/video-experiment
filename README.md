# Video Experiment (oTree)

An oTree survey: screening tasks, three short self-introduction videos recorded with automatic background blur (Chrome), belief elicitation, and post-survey questionnaires.

## Run locally

```
pip install -r requirements.txt
otree devserver
```

Open http://localhost:8000/demo and use Google Chrome. The walk-through sessions let you click through without answering.

## Configuration

Study-specific details are not stored in this repository. Set them as environment variables, or in a local `study.env` file (git-ignored):

`PROLIFIC_COMPLETION_URL`, `CONSENT_INSTITUTIONS`, `CONSENT_STUDY_ID`, `CONSENT_SPONSOR`, `CONSENT_DISCLOSING_INSTITUTION`, `CONSENT_CONTACT_NAME`, `CONSENT_CONTACT_EMAIL`, `CONSENT_IRB_CONTACT`

Videos are uploaded to a Box folder if Box credentials are set (in a git-ignored `box.env`). See the top of `video_upload.py` for setup.

## Deploy

`render.yaml` deploys a free demo on Render (New → Blueprint).
