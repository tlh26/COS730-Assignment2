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

# ================DATABASE (LOW LEVEL)==============================

class Database:
    def __init__(self):
        self.submission_file = "submissions.txt"
        self.score_file = "scores.txt"

    def insert_submission(self, data):
        with open(self.submission_file, "a") as f:
            f.write(f"{data['title']}|{data['content']}\n")

    def insert_score(self, submission_id, reviewer, score):
        with open(self.score_file, "a") as f:
            f.write(f"{submission_id}|{reviewer}|{score}\n")

    def read_scores(self):
        try:
            with open(self.score_file, "r") as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            return []

    def read_submissions(self):
        try:
            with open(self.submission_file, "r") as f:
                return f.readlines()
        except FileNotFoundError:
            return []



# ======================= DATABASE MANAGER =====================
class DatabaseManager:
    def __init__(self):
        self.db = Database()

    @metrics.track("DBM.saveSubmission")
    def saveSubmission(self, data):
        print("DatabaseManager: saveSubmission")
        self.db.insert_submission(data)
        return {"id": self._get_submission_count(), **data}

    @metrics.track("DBM.fetchReviewers")
    def fetchReviewers(self):
        print("DatabaseManager: fetchReviewers")

        # Simulated DB data
        return [
            {"name": "Jan Doey", "expertise": "AI"},
            {"name": "Jane Smith", "expertise": "Security"},
            {"name": "John Doe", "expertise": "AI"},
        ]

    @metrics.track("DBM.getReviewerWorkload")
    def getReviewerWorkload(self, reviewer_name):
        print(f"DatabaseManager: workload for {reviewer_name}")

        count = 0
        for line in self.db.read_scores():
            parts = line.split("|")
            if len(parts) != 3:
                continue

            _, reviewer, _ = parts
            if reviewer == reviewer_name:
                count += 1

        return count

    @metrics.track("DBM.saveScore")
    def saveScore(self, submission_id, reviewer, score):
        print("DatabaseManager: saveScore")
        self.db.insert_score(submission_id, reviewer, score)

    @metrics.track("DBM.getScores")
    def getScores(self, submission_id):
        print("DatabaseManager: getScores")

        scores = []
        for line in self.db.read_scores():
            parts = line.split("|")
            if len(parts) != 3:
                continue

            sid, _, score = parts
            if int(sid) == submission_id:
                scores.append(int(score))

        return scores

    def _get_submission_count(self):
        return len(self.db.read_submissions())


# ======================= CONTROLLER =====================
class SubmissionController:
    def __init__(self):
        self.validator = Validator()
        self.db_manager = DatabaseManager()
        self.reviewer_manager = ReviewerManager(self.db_manager)
        self.evaluator = EvaluationManager(self.db_manager)
        self.notifier = NotificationService()

    @metrics.track("Controller.submit")
    def submit(self, data):
        print("\n--- Submission Started ---")

        # Validation
        is_valid = self.validator.validate(data)

        if not is_valid:
            print("Controller: return error")
            return "Error"

        # Save
        submission = self.db_manager.saveSubmission(data)

        # Reviewer selection (encapsulated)
        reviewers = self.reviewer_manager.selectReviewers(submission)

        # Assign reviewers
        for r in reviewers:
            self.reviewer_manager.assignReview(r)

        # Evaluation (centralised)
        decision = self.evaluator.evaluateSubmission(submission, reviewers)

        # Notify
        self.notifier.notify(decision)

        print("--- Submission Completed ---\n")
        return decision


# ======================= VALIDATOR =====================
class Validator:
    @metrics.track("Validator.validate")
    def validate(self, data):
        print("Validator: validate")
        return data.get("valid", True)

# ======================= REVIEWER MANAGER =====================
class ReviewerManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    @metrics.track("ReviewerManager.selectReviewers")
    def selectReviewers(self, submission):
        print("ReviewerManager: selectReviewers")

        reviewers = self.db_manager.fetchReviewers()

        reviewers = self._filterConflicts(reviewers, submission)
        reviewers = self._filterWorkload(reviewers)

        return [r["name"] for r in reviewers]

    def _filterConflicts(self, reviewers, submission):
        print("Filtering conflicts")

        return [
            r for r in reviewers
            if r["name"] not in submission["title"]
        ]

    def _filterWorkload(self, reviewers):
        print("Filtering workload")

        available = []
        for r in reviewers:
            workload = self.db_manager.getReviewerWorkload(r["name"])
            if workload < 2:
                available.append(r)

        return available

    @metrics.track("ReviewerManager.assignReview")
    def assignReview(self, reviewer):
        print(f"Assigning {reviewer}")

# ======================= EVALUATION MANAGER =====================
class EvaluationManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    @metrics.track("EvaluationManager.evaluateSubmission")
    def evaluateSubmission(self, submission, reviewers):
        print("EvaluationManager: evaluateSubmission")

        # No reviewers assigned
        if not reviewers:
            print("No reviewers available for this submission")
            return "no_reviewers"

        # Simulate scoring
        for r in reviewers:
            score = self._simulate_score(r)
            self.db_manager.saveScore(submission["id"], r, score)

        scores = self.db_manager.getScores(submission["id"])

        return self._computeDecision(scores)

    def _simulate_score(self, reviewer):
        return len(reviewer) + 5

    def _computeDecision(self, scores):
        print("Computing decision")

        if not scores:
            print("WARNING: No scores found")
            return "no_scores"

        avg = sum(scores) / len(scores)

        if len(scores) < 2:
            consensus = False
        else:
            consensus = max(scores) - min(scores) < 3

        if avg >= 7 and consensus:
            return "accepted"
        elif avg < 4:
            return "rejected"
        return "revision"
    

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

# ======================= NOTIFICATION =====================
class NotificationService:
    @metrics.track("Notification.notify")
    def notify(self, decision):
        if decision == "accepted":
            print("Notification: accepted")
        elif decision == "rejected":
            print("Notification: rejected")
        elif decision == "revision":
            print("Notification: revision required")
        elif decision == "no_reviewers":
            print("Notification: no reviewers available")
        elif decision == "no_scores":
            print("Notification: evaluation incomplete")

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