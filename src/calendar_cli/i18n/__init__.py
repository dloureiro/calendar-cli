import os
import locale


def __get_locale():
    # environment LANG is the first priority
    lang = os.environ.get('LANG')
    if lang:
        return lang.lower()
    return locale.getdefaultlocale()[0].lower()


__locale = __get_locale()

if __locale.startswith('ja_'):
    from .messages_ja import *
elif __local.startswith('fr_'):
	from .messages_fr import *
else:
    from .messages_en import *
