from otree.api import Bot, Submission, SubmissionMustFail, expect
from . import *


class PlayerBot(Bot):
    def play_round(self):
        yield Submission(JobPosting, check_html=False)
        yield Submission(ResumeInfo, check_html=False)
        yield Submission(VideoInstructions, check_html=False)
        correct = {f: c for f, _, _, c in C.COMPREHENSION}
        yield SubmissionMustFail(Comprehension, {**correct, 'comp_2': 1})
        yield Comprehension, correct
        expect(self.player.comp_failed_attempts, 1)
        yield VideoName, dict(video_name='Alex')
        expect('Alex', 'in', self.html)
        yield VideoA, dict(video_a_recorded=True, video_a_seconds=31.5, video_a_takes=1)
        yield VideoB, dict(video_b_recorded=True, video_b_seconds=40.0, video_b_takes=3)
        yield VideoC, dict(video_c_recorded=True, video_c_seconds=12.2, video_c_takes=2)
        expect(self.player.field_maybe_none('video_a_uploaded'), True)
        expect(self.player.video_a_file, 'in', ' '.join(__import__('os').listdir('video_uploads/pending')))
        expect('CHECK', 'in', self.html)
        expect(C.PROMPT_SETS[self.session.config['prompt_set']]['b'], 'in', self.html)
        yield HireBeliefs, dict(hire_belief_a=60, hire_belief_b=45, hire_belief_c=70)
        yield SubmissionMustFail(HireRanking, dict(rank_a=1, rank_b=1, rank_c=3))
        yield HireRanking, dict(rank_a=2, rank_b=3, rank_c=1)
        expect(self.player.prompt_set, self.session.config['prompt_set'])
        expect('limited time', 'in', self.html)
        yield ChooseVideo, dict(video_sent='c')
        bad = {f'mpl_{i}': (1 if i in (1, 3) else 0) for i in range(1, 12)}
        yield SubmissionMustFail(AdditionalVideoMPL, {**bad, 'mpl_extra_video': 'a'})
        yield SubmissionMustFail(AdditionalVideoMPL, {**{f'mpl_{i}': 0 for i in range(1, 12)}, 'mpl_extra_video': 'c'})
        good = {f'mpl_{i}': (1 if i <= 4 else 0) for i in range(1, 12)}
        yield AdditionalVideoMPL, {**good, 'mpl_extra_video': 'a'}
        expect(self.player.mpl_max_wtp, 0.30)


def call_live_method(method, page_class, **kwargs):
    """Send a small fake video through the chunked upload on Video A."""
    import base64
    if page_class.__name__ != 'VideoA':
        return
    import asyncio
    raw_method = method

    def method(pid, payload):  # oTree 6 returns an async generator here
        async def first():
            async for r in raw_method(pid, payload):
                return r
        return asyncio.new_event_loop().run_until_complete(first())

    for pid in [p.id_in_group for p in kwargs['group'].get_players()]:
        data = b'fake-webm-' * 50000  # ~500 KB -> 2 chunks
        letter = 'a'
        r = method(pid, dict(type='start', letter=letter, size=len(data), mime='video/webm'))
        expect(r[pid]['type'], 'ready')
        expect(method(pid, dict(type='chunk', letter=letter, offset=5, data='AAAA'))[pid]['offset'], 0)  # resync
        offset = 0
        while offset < len(data):
            part = data[offset:offset + 262144]
            r = method(pid, dict(type='chunk', letter=letter, offset=offset, data=base64.b64encode(part).decode()))
            expect(r[pid]['type'], 'ack')
            offset = r[pid]['offset']
        expect(method(pid, dict(type='done', letter=letter))[pid]['type'], 'stored')
        expect(method(pid, dict(type='chunk', letter='z', offset=0, data=''))[pid]['type'], 'error')
