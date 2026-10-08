import unittest
from unittest.mock import patch

import main


class StepRangeTests(unittest.TestCase):
    def test_configured_limits_scale_until_22(self):
        with patch.object(main, "config", {"MIN_STEP": "15000", "MAX_STEP": "18000"}, create=True):
            self.assertEqual(main.get_min_max_by_time(11, 0), (7500, 9000))
            self.assertEqual(main.get_min_max_by_time(22, 0), (15000, 18000))
            self.assertEqual(main.get_min_max_by_time(23, 59), (15000, 18000))


class ExecutionTests(unittest.TestCase):
    def execute_with_results(self, results, concurrent=False):
        with patch.multiple(
            main,
            users="#".join(f"user{i}" for i in range(len(results))),
            passwords="#".join("password" for _ in results),
            use_concurrent=concurrent,
            sleep_seconds=0,
            encrypt_support=False,
            push_config=None,
            create=True,
        ), patch.object(main, "run_single_account", side_effect=results), patch.object(
            main.push_util, "push_results"
        ) as push:
            main.execute()
            self.assertEqual(len(push.call_args.args[0]), len(results))

    def test_success(self):
        self.execute_with_results([{"success": True}])

    def test_failure_exits_nonzero(self):
        with self.assertRaises(SystemExit) as error:
            self.execute_with_results([{"success": False}])
        self.assertEqual(error.exception.code, 1)

    def test_partial_failure_exits_nonzero(self):
        with self.assertRaises(SystemExit) as error:
            self.execute_with_results([{"success": True}, {"success": False}])
        self.assertEqual(error.exception.code, 1)

    def test_concurrent_failure_exits_nonzero(self):
        with self.assertRaises(SystemExit) as error:
            self.execute_with_results([{"success": False}], concurrent=True)
        self.assertEqual(error.exception.code, 1)

    def test_mismatched_credentials_exit_nonzero(self):
        with patch.multiple(main, users="one#two", passwords="password", create=True):
            with self.assertRaises(SystemExit) as error:
                main.execute()
        self.assertEqual(error.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
