import unittest
from datetime import datetime, timezone
from pathlib import Path
import re
from unittest.mock import patch
from zoneinfo import ZoneInfo

import main


class WorkflowScheduleTests(unittest.TestCase):
    def test_three_fixed_runs_in_beijing_time(self):
        workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/run.yml").read_text()
        schedules = re.findall(r"- cron: '([^']+)'", workflow)
        self.assertEqual(schedules, ["0 7,15,23 * * *"])
        minute, hours, day, month, weekday = schedules[0].split()
        self.assertEqual((minute, day, month, weekday), ("0", "*", "*", "*"))
        beijing_hours = sorted(
            datetime(2026, 10, 9, int(hour), tzinfo=timezone.utc)
            .astimezone(ZoneInfo("Asia/Shanghai")).hour
            for hour in hours.split(",")
        )
        self.assertEqual(beijing_hours, [7, 15, 23])

    def test_randomization_cannot_run_automatically(self):
        workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/cron.yml").read_text()
        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("workflow_run:", workflow)
        self.assertNotRegex(workflow, r"(?m)^\s+schedule:")


class StepRangeTests(unittest.TestCase):
    def test_fixed_minimum_with_24_hour_bonus(self):
        with patch.object(main, "config", {"MIN_STEP": "15000", "MAX_STEP": "18000"}, create=True):
            for hour, minute, upper in [
                (0, 0, 15000),
                (6, 0, 15750),
                (12, 0, 16500),
                (18, 0, 17250),
                (20, 0, 17500),
                (22, 0, 17750),
                (23, 59, 17997),
            ]:
                with self.subTest(hour=hour, minute=minute):
                    self.assertEqual(main.get_min_max_by_time(hour, minute), (15000, upper))

    def test_every_minute_stays_within_limits(self):
        with patch.object(main, "config", {"MIN_STEP": "15000", "MAX_STEP": "18000"}, create=True):
            previous_upper = 15000
            for elapsed in range(1440):
                lower, upper = main.get_min_max_by_time(*divmod(elapsed, 60))
                self.assertEqual(lower, 15000)
                self.assertEqual(upper, 15000 + 3000 * elapsed // 1440)
                self.assertLessEqual(previous_upper, upper)
                self.assertLessEqual(upper, 18000)
                previous_upper = upper

    def test_current_beijing_time_and_midnight_reset(self):
        with patch.object(main, "config", {"MIN_STEP": "15000", "MAX_STEP": "18000"}, create=True):
            with patch.object(main, "time_bj", datetime(2026, 10, 9, 23, 59), create=True):
                self.assertEqual(main.get_min_max_by_time(), (15000, 17997))
            with patch.object(main, "time_bj", datetime(2026, 10, 10, 0, 0), create=True):
                self.assertEqual(main.get_min_max_by_time(), (15000, 15000))

    def test_equal_limits(self):
        with patch.object(main, "config", {"MIN_STEP": "15000", "MAX_STEP": "15000"}, create=True):
            self.assertEqual(main.get_min_max_by_time(12, 0), (15000, 15000))

    def test_invalid_limits_raise(self):
        for minimum, maximum in [(-1, 18000), (18000, 15000)]:
            with self.subTest(minimum=minimum, maximum=maximum):
                with patch.object(main, "config", {"MIN_STEP": minimum, "MAX_STEP": maximum}, create=True):
                    with self.assertRaisesRegex(ValueError, "Step limits"):
                        main.get_min_max_by_time(12, 0)

    def test_randomized_total_is_submitted(self):
        for selected in (15000, 16500):
            with self.subTest(selected=selected):
                with patch.object(main, "user_tokens", {}, create=True), patch.object(
                    main.MiMotionRunner, "login", return_value="test-token"
                ), patch.object(main.random, "randint", return_value=selected) as randint, patch.object(
                    main.zeppHelper, "post_fake_brand_data", return_value=(True, "success")
                ) as post:
                    runner = main.MiMotionRunner("example@example.com", "test-password")
                    message, success = runner.login_and_post_step(15000, 16500)
                    randint.assert_called_once_with(15000, 16500)
                    post.assert_called_once_with(str(selected), "test-token", None, device_id=None)
                    self.assertTrue(success)
                    self.assertIn(str(selected), message)


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
