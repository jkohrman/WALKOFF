import unittest
import uuid

from core.executionelements.transform import Transform
from core.executionelements.condition import Condition
from core.helpers import InvalidInput
from tests.config import test_apps_path
import core.config.config
import apps


class TestCondition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        apps.clear_cache()
        apps.cache_apps(path=test_apps_path)
        core.config.config.load_app_apis(test_apps_path)

    @classmethod
    def tearDownClass(cls):
        apps.clear_cache()

    def __compare_init(self, condition, app, action, transforms, args, uid=None):
        self.assertEqual(condition.app, app)
        self.assertEqual(condition.action, action)
        self.assertEqual(len(condition.transforms), len(transforms))
        for actual_transform, expected_transform in zip(condition.transforms, transforms):
            self.assertDictEqual(actual_transform.read(), expected_transform.read())
        self.assertDictEqual(condition.args, args)
        if uid is None:
            self.assertIsNotNone(condition.uid)
        else:
            self.assertEqual(condition.uid, uid)

    def test_init_no_args_action_only(self):
        condition = Condition('HelloWorld', 'Top Condition')
        self.__compare_init(condition, 'HelloWorld',  'Top Condition', [], {})

    def test_init_with_uid(self):
        uid = uuid.uuid4().hex
        condition = Condition('HelloWorld', 'Top Condition', uid=uid)
        self.__compare_init(condition, 'HelloWorld', 'Top Condition', [], {}, uid=uid)

    def test_init_with_args_with_conversion(self):
        condition = Condition('HelloWorld', 'mod1_flag2', args={'arg1': '3'})
        self.__compare_init(condition, 'HelloWorld', 'mod1_flag2', [], {'arg1': 3})

    def test_init_with_args_no_conversion(self):
        condition = Condition('HelloWorld', 'mod1_flag2', args={'arg1': 3})
        self.__compare_init(condition, 'HelloWorld', 'mod1_flag2', [], {'arg1': 3})

    def test_init_with_args_with_routing(self):
        condition = Condition('HelloWorld', 'mod1_flag2', args={'arg1': '@step2'})
        self.__compare_init(condition , 'HelloWorld', 'mod1_flag2', [], {'arg1': '@step2'})

    def test_init_with_args_invalid_arg_name(self):
        with self.assertRaises(InvalidInput):
            Condition('HelloWorld', 'mod1_flag2', args={'invalid': '3'})

    def test_init_with_args_invalid_arg_type(self):
        with self.assertRaises(InvalidInput):
            Condition('HelloWorld', 'mod1_flag2', args={'arg1': 'aaa'})

    def test_init_with_transforms(self):
        transforms = [Transform('HelloWorld', 'mod1_filter2', args={'arg1': '5.4'}), Transform('HelloWorld', 'Top Transform')]
        condition = Condition('HelloWorld', 'Top Condition', transforms=transforms)
        self.__compare_init(condition , 'HelloWorld', 'Top Condition', transforms, {})

    def test_execute_action_only_no_args_valid_data_no_conversion(self):
        self.assertTrue(Condition('HelloWorld', 'Top Condition').execute(3.4, {}))

    def test_execute_action_only_no_args_valid_data_with_conversion(self):
        self.assertTrue(Condition('HelloWorld', 'Top Condition').execute('3.4', {}))

    def test_execute_action_only_no_args_invalid_data(self):
        self.assertFalse(Condition('HelloWorld', 'Top Condition').execute('invalid', {}))

    def test_execute_action_with_valid_args_valid_data(self):
        self.assertTrue(Condition('HelloWorld', 'mod1_flag2', args={'arg1': 3}).execute('5', {}))

    def test_execute_action_with_valid_complex_args_valid_data(self):
        self.assertTrue(Condition('HelloWorld', 'mod1_flag3', args={'arg1': {'a': '1', 'b': '5'}}).execute('some_long_string', {}))

    def test_execute_action_with_valid_args_invalid_data(self):
        self.assertFalse(Condition('HelloWorld', 'mod1_flag2', args={'arg1': 3}).execute('invalid', {}))

    def test_execute_action_with_valid_args_and_transforms_valid_data(self):
        transforms = [Transform('HelloWorld', 'mod1_filter2', args={'arg1': '5'}), Transform('HelloWorld', 'Top Transform')]
        # should go <input = 1> -> <mod1_filter2 = 5+1 = 6> -> <Top Transform 6=6> -> <mod1_flag2 4+6%2==0> -> True
        self.assertTrue(Condition('HelloWorld', 'mod1_flag2', args={'arg1': 4}, transforms=transforms).execute('1', {}))

    def test_execute_action_with_valid_args_and_transforms_invalid_data(self):
        transforms = [Transform('HelloWorld', 'mod1_filter2', args={'arg1': '5'}), Transform('HelloWorld', 'Top Transform')]
        # should go <input = invalid> -> <mod1_filter2 with error = invalid> -> <Top Transform with error = invalid>
        # -> <mod1_flag2 4+invalid throws error> -> False
        self.assertFalse(Condition('HelloWorld', 'mod1_flag2', args={'arg1': 4}, transforms=transforms).execute('invalid', {}))

    def test_execute_action_with_valid_args_and_transforms_invalid_data_and_routing(self):
        transforms = [Transform('HelloWorld', 'mod1_filter2', args={'arg1': '@step1'}), Transform('HelloWorld', 'Top Transform')]
        # should go <input = invalid> -> <mod1_filter2 with error = invalid> -> <Top Transform with error = invalid>
        # -> <mod1_flag2 4+invalid throws error> -> False
        accumulator = {'step1': '5', 'step2': 4}
        self.assertFalse(Condition('HelloWorld', 'mod1_flag2', args={'arg1': 4}, transforms=transforms).execute('invalid', accumulator))