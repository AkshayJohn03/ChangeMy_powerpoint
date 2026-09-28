"""Color math sanity: the mapping quality depends entirely on these."""

from brandmorph.engine.colorutil import (
    delta_e76,
    hex_delta,
    hex_to_lab,
    normalize_hex,
    rgb_to_hls,
    shade,
)


def test_normalize_hex():
    assert normalize_hex("#030c1e") == "030C1E"
    assert normalize_hex("f81") == "FF8811"


def test_lab_endpoints():
    white = hex_to_lab("FFFFFF")
    black = hex_to_lab("000000")
    assert abs(white[0] - 100) < 0.5
    assert abs(black[0]) < 0.5


def test_red_is_closer_to_danger_than_gold():
    # role-preserving mapping depends on this ordering holding
    red = hex_to_lab("FF0000")
    danger = hex_to_lab("E5484D")
    gold = hex_to_lab("FFB81C")
    assert delta_e76(red, danger) < delta_e76(red, gold)


def test_navy_and_black_are_perceptually_close():
    # the reason we use Lab, not RGB distance: RGB distance here is ~30,
    # Lab delta-E says "same visual family" (~12.6)
    assert hex_delta("030C1E", "000000") < 15


def test_shade_moves_lightness_monotonically():
    base = hex_to_lab("FFB81C")[0]
    lighter = hex_to_lab(shade("FFB81C", 12.0))[0]
    darker = hex_to_lab(shade("FFB81C", -12.0))[0]
    assert lighter > base > darker


def test_hls_saturation_gate():
    _, _l, s_white = rgb_to_hls(255, 255, 255)
    _, _l, s_red = rgb_to_hls(255, 0, 0)
    assert s_white == 0.0
    assert s_red > 0.9
