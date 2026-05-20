from secrets import token_urlsafe


def issue_player_token() -> str:
    return token_urlsafe(24)