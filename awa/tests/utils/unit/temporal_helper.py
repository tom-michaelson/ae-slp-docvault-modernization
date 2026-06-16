from temporalio.testing import ActivityEnvironment


class TemporalHelper:
    @staticmethod
    def get_activity_environment() -> ActivityEnvironment:
        return ActivityEnvironment()
