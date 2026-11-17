"""Several keys (e.g. W/A/S/D on a keyboard) act as one pedal button."""

from types import SimpleNamespace
import unittest

from pika_foot_pedal.node import FootPedalNode

KEY_W, KEY_A, KEY_S, KEY_D, KEY_Q = 17, 30, 31, 32, 16


def make_node(setting):
    node = FootPedalNode.__new__(FootPedalNode)
    node.key_setting = setting
    node.key_codes = set()
    node._held_codes = set()
    node._resolve_key_setting()
    return node


def event(code, value, usec=0):
    return SimpleNamespace(code=code, value=value, sec=1, usec=usec)


class TestMultiKey(unittest.TestCase):
    def test_numeric_list_is_parsed(self):
        node = make_node(f'{KEY_W}, {KEY_A},{KEY_S} ,{KEY_D}')
        assert node.key_codes == {KEY_W, KEY_A, KEY_S, KEY_D}

    def test_auto_leaves_codes_unset(self):
        assert make_node('auto').key_codes == set()

    def test_empty_list_is_rejected(self):
        with self.assertRaises(ValueError):
            make_node(' , ')

    def test_key_names_resolve_when_evdev_is_available(self):
        try:
            import evdev  # noqa: F401
        except ImportError:
            self.skipTest('python3-evdev not installed')
        assert make_node('KEY_W,KEY_A,KEY_S,KEY_D').key_codes == {KEY_W, KEY_A, KEY_S, KEY_D}

    def test_unknown_key_name_is_rejected(self):
        try:
            import evdev  # noqa: F401
        except ImportError:
            self.skipTest('python3-evdev not installed')
        with self.assertRaises(ValueError):
            make_node('KEY_W,KEY_NOT_A_KEY')

    def test_any_listed_key_presses_and_releases(self):
        node = make_node(f'{KEY_W},{KEY_A},{KEY_S},{KEY_D}')
        for code in (KEY_W, KEY_A, KEY_S, KEY_D):
            merged = node._merge_key_events([event(code, 1), event(code, 0)])
            assert [e.value for e in merged] == [1, 0]

    def test_overlapping_keys_count_as_one_press(self):
        node = make_node(f'{KEY_W},{KEY_A},{KEY_S},{KEY_D}')
        merged = node._merge_key_events([
            event(KEY_W, 1, 0), event(KEY_A, 1, 10), event(KEY_W, 0, 20), event(KEY_A, 0, 30),
        ])
        assert [(e.value, e.usec) for e in merged] == [(1, 0), (0, 30)]

    def test_unlisted_keys_are_ignored(self):
        node = make_node(f'{KEY_W},{KEY_A},{KEY_S},{KEY_D}')
        assert node._merge_key_events([event(KEY_Q, 1), event(KEY_Q, 0)]) == []

    def test_release_without_press_is_no_edge(self):
        node = make_node(f'{KEY_W}')
        assert node._merge_key_events([event(KEY_W, 0)]) == []

    def test_single_key_behaves_as_before(self):
        node = make_node(f'{KEY_W}')
        merged = node._merge_key_events([event(KEY_W, 1), event(KEY_W, 0)])
        assert [e.value for e in merged] == [1, 0]
