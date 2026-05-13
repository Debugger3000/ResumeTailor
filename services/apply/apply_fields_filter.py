
import re


CAPTCHA_PATTERN = re.compile(
    r"(?:"
    r"h[-_]?captcha"            # hcaptcha, h-captcha, h_captcha
    r"|re[-_]?captcha"          # recaptcha, re-captcha
    r"|g[-_]?recaptcha"         # g-recaptcha-response
    r"|cf[-_]?turnstile"        # cloudflare turnstile
    r"|turnstile[-_]?response"
    r"|arkose"                   # arkose labs
    r"|fun[-_]?captcha"
    r"|\bcaptcha\b"             # generic
    r")",
    re.IGNORECASE,
)



def filter_fields(fields: list[dict]) -> list[dict]:
    """
    Drop fields that should never be sent to the model:
      - file uploads (handled separately)
      - captcha fields (hCaptcha, reCAPTCHA, Turnstile, etc.)
    """
    out = []
    for f in fields:
        if f.get('kind') == 'file' or f.get('input_type') == 'file':
            continue

        haystack = ' '.join([
            f.get('name') or '',
            f.get('question') or '',
        ])
        if CAPTCHA_PATTERN.search(haystack):
            continue

        out.append(f)
    return out






