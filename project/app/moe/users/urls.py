# -*- coding: utf-8 -*-
"""
    urls
    ~~~~

    URL definitions.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from tipfy import Rule

def get_rules():
    rules = [
        Rule('/account/new', endpoint='users/new', handler='moe.users.handlers.SignupHandler'),
        Rule('/account/signup', endpoint='auth/signup', handler='moe.users.handlers.SignupHandler'),
        Rule('/account/login', endpoint='auth/login', handler='moe.users.handlers.LoginHandler'),
        Rule('/account/logout', endpoint='auth/logout', handler='moe.users.handlers.LogoutHandler'),
        Rule('/account/forgot-password', endpoint='users/forgot-password', handler='moe.users.handlers.ForgotPasswordHandler'),
        Rule('/profiles/<username>', endpoint='users/profile', handler='moe.users.handlers.ProfileHandler'),
    ]

    return rules
