"""
Walk-through mode (session config ``walkthrough=True``).

Lets you click through the whole study without answering anything:
- client side (_static/global/js/walkthrough.js): the Next button is always
  shown and enabled, page-level "required" checks are bypassed, and any
  unanswered required inputs are filled with placeholder answers on submit
  (so oTree's own field validation passes);
- server side (this module): custom answer checks (error_message) are skipped
  and screen-out pages (pages with ``screen_out = True``) are never shown.

Data from walk-through sessions is placeholder data and should not be analysed.
"""


def is_on(player) -> bool:
    return bool(player.session.config.get('walkthrough', False))


def apply(page_sequence):
    for P in page_sequence:
        if hasattr(P, 'error_message'):
            orig_em = P.error_message

            def error_message(player, values, _orig=orig_em):
                if is_on(player):
                    return None
                return _orig(player, values)

            P.error_message = staticmethod(error_message)

        if getattr(P, 'screen_out', False):
            orig_disp = P.is_displayed

            def is_displayed(player, _orig=orig_disp):
                if is_on(player):
                    return False
                return _orig(player)

            P.is_displayed = staticmethod(is_displayed)
