from smart_money.adapters.bsc_discovery import decode_bsc_activity, rank_bsc_candidates


def test_bsc_activity_decoder_and_ranking():
    wallet = "0x2c26f58bba087d83c43c19b4761042320c5beaf4"
    activity = decode_bsc_activity(({"to": wallet, "token": "T", "value": "1"},), wallet)
    assert activity[0]["direction"] == "BUY"
    assert rank_bsc_candidates(activity)[0]["chain"] == "bsc"
