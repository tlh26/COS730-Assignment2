import time
from collections import defaultdict


# ============================ METRICS =============================
class Metrics:
    def __init__(self):
        self.call_count = defaultdict(int)
        self.execution_time = defaultdict(float)

    def track(self, name):
        def decorator(func):
            def wrapper(*args, **kwargs):
                start = time.perf_counter()

                self.call_count[name] += 1
                result = func(*args, **kwargs)

                end = time.perf_counter()
                self.execution_time[name] += (end - start)

                return result
            return wrapper
        return decorator

    def report(self):
        print("\n=== METRICS REPORT ===")

        print("\nMethod Calls:")
        for k, v in self.call_count.items():
            print(f"{k}: {v}")

        print("\nExecution Time (seconds):")
        for k, v in self.execution_time.items():
            print(f"{k}: {v:.6f}")
metrics = Metrics()


# ======================== BASELINE SYSTEM ==================

class SubmissionController:
    def __init__(self):
        self.validator = Validator()
        self.db = Database()
        self.reviewer_manager = ReviewerManager(self.db)
        self.evaluator = EvaluationManager()
        self.notifier = NotificationService()

    def submit(self, data):
        print("\n--- Submission Started ---")

        # validateFormat
        is_valid = self.validator.validateFormat(data)

        if not is_valid:
            print("SubmissionController: return error")
            return "Error: Invalid data"

        # saveSubmission
        submission = self.db.save_submission(data)

        # getAvailableReviewers
        reviewer_list = self.reviewer_manager.getAvailableReviewers(submission)

        # assignReview LOOP
        assigned_reviewers = []
        for reviewer_name in reviewer_list:
            reviewer = Reviewer(reviewer_name)
            print(f"assignReview() -> {reviewer.name}")
            assigned_reviewers.append(reviewer)

        print("startEvaluation()")

        # LOOP reviewers
        for reviewer in assigned_reviewers:
            score = self.simulate_score(reviewer.name)

            reviewer.submitScore(score)

            # saveScore
            self.db.save_score(score, reviewer.name, submission["id"])

        # calculateAverage
        scores = self.db.load_scores(submission["id"])
        avg = self.evaluator.calculateAverage(scores)

        # checkConsensus
        consensus = self.evaluator.checkConsensus(scores)

        # applyRules
        decision = self.evaluator.applyRules(avg, consensus, scores)

        # notify
        if decision == "accepted":
            self.notifier.notifyAcceptance()
        elif decision == "rejected":
            self.notifier.notifyRejection()
        elif decision == "no_reviewers":
            print("No reviewers available")
        else:
            self.notifier.notifyRevision()

        print("--- Submission Completed ---\n")
        return decision

    def simulate_score(self, reviewer_name):
        return len(reviewer_name) + 5


# ======================== VALIDATOR ========================
class Validator:
    @metrics.track("validateFormat")
    def validateFormat(self, data):
        print("validateFormat(data)")
        return data.get("valid", True)


# ======================== REVIEWER MANAGER ========================
class ReviewerManager:
    def __init__(self, db):
        self.db = db

    @metrics.track("getAvailableReviewers")
    def getAvailableReviewers(self, submission):
        print("getAvailableReviewers()")

        reviewers = self.fetchReviewers()
        reviewers = self.filterConflicts(reviewers, submission)
        reviewers = self.checkWorkload(reviewers)

        return reviewers

    @metrics.track("fetchReviewers")
    def fetchReviewers(self):
        print("fetchReviewers()")

        # Simulated reviewer pool
        return [
            {"name": "Jan Doey", "expertise": "AI"},
            {"name": "Jane Smith", "expertise": "Security"},
            {"name": "John Doe", "expertise": "AI"},
        ]

    @metrics.track("filterConflicts")
    def filterConflicts(self, reviewers, submission):
        print("filterConflicts()")

        filtered = []
        for r in reviewers:
            # simulate conflict: reviewer name appears in submission title
            if r["name"] not in submission["title"]:
                filtered.append(r)
            else:
                print(f"Conflict detected for {r['name']}")

        return filtered

    @metrics.track("checkWorkload")
    def checkWorkload(self, reviewers):
        print("checkWorkload()")

        available = []
        for r in reviewers:
            workload = self.db.get_reviewer_workload(r["name"])

            print(f"{r['name']} workload: {workload}")

            # simple rule: max 2 active reviews
            if workload < 2:
                available.append(r)
            else:
                print(f"{r['name']} overloaded")

        # return only names
        return [r["name"] for r in available]


# ======================== REVIEWER ========================
class Reviewer:
    def __init__(self, name):
        self.name = name

    @metrics.track("submitScore")
    def submitScore(self, score):
        print(f"{self.name} -> submitScore({score})")


# ======================== EVALUATION ========================
class EvaluationManager:
    @metrics.track("calculateAverage")
    def calculateAverage(self, scores):
        print("calculateAverage()")

        if not scores:
            print("WARNING: No scores available")
            return 0  # neutral fallback

        return sum(scores) / len(scores)

    @metrics.track("checkConsensus")
    def checkConsensus(self, scores):
        print("checkConsensus()")
        if len(scores) < 2:
            return False
        return max(scores) - min(scores) < 3

    @metrics.track("applyRules")
    def applyRules(self, avg, consensus, scores):
        print("applyRules()")

        if not scores:
            return "no_reviewers"

        if avg >= 7 and consensus:
            return "accepted"
        elif avg < 4:
            return "rejected"
        return "revision"


# ======================= NOTIFICATION ========================
class NotificationService:
    @metrics.track("notifyAcceptance")
    def notifyAcceptance(self):
        print("notifyAcceptance()")

    @metrics.track("notifyRejection")
    def notifyRejection(self):
        print("notifyRejection()")

    @metrics.track("notifyRevision")
    def notifyRevision(self):
        print("notifyRevision()")

# ================ DATABASE =========================
class Database:
    def __init__(self):
        self.submission_file = "submissions.txt"
        self.score_file = "scores.txt"

    @metrics.track("saveSubmission")
    def save_submission(self, data):
        print("Database: saving submission")

        with open(self.submission_file, "a") as f:
            record = f"{data['title']}|{data['content']}\n"
            f.write(record)

        return {"id": self._get_submission_count(), **data}

    @metrics.track("saveScore")
    def save_score(self, score, reviewer, submission_id):
        print(f"Database: saving score {score}")

        with open(self.score_file, "a") as f:
            f.write(f"{submission_id}|{reviewer}|{score}\n")

    @metrics.track("loadScores")
    def load_scores(self, submission_id):
        print("Database: loading scores")

        scores = []
        try:
            with open(self.score_file, "r") as f:
                for line in f:
                    sid, reviewer, score = line.strip().split("|")
                    if int(sid) == submission_id:
                        scores.append(int(score))
        except FileNotFoundError:
            pass

        return scores

    @metrics.track("getReviewerWorkload")
    def get_reviewer_workload(self, reviewer_name):
        print(f"Database: checking workload for {reviewer_name}")

        count = 0
        try:
            with open(self.score_file, "r") as f:
                for line in f:
                    _, reviewer, _ = line.strip().split("|")
                    if reviewer == reviewer_name:
                        count += 1
        except FileNotFoundError:
            pass

        return count

    def _get_submission_count(self):
        try:
            with open(self.submission_file, "r") as f:
                return len(f.readlines())
        except FileNotFoundError:
            return 0

def run_benchmark(controller_class, runs=10):
    print(f"\n=== Running Benchmark ({runs} runs) ===")

    controller = controller_class()

    data = {
        "title": "AI Research Paper",
        "content": "Some content",
        "valid": True
    }

    start = time.perf_counter()

    for _ in range(runs):
        controller.submit(data)

    end = time.perf_counter()

    total_time = end - start
    avg_time = total_time / runs

    print("\n=== BENCHMARK RESULTS ===")
    print(f"Total Execution Time: {total_time:.6f} seconds")
    print(f"Average Time per Run: {avg_time:.6f} seconds")

    metrics.report()

# ======================== RUN ========================
if __name__ == "__main__":
    run_benchmark(SubmissionController, runs=5)
    # controller = SubmissionController()

    # data = {
    #     "title": "AI Research Paper",
    #     "content": "Some content",
    #     "valid": True
    # }

    # controller.submit(data)

    # metrics.report()
    