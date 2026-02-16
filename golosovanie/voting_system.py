class Poll:
    def __init__(self, question: str, options: list[str]):
        if not question or not question.strip():
            raise ValueError("Вопрос опроса не может быть пустым")
        if len(options) < 2:
            raise ValueError("Должно быть минимум 2 варианта ответа")
        stripped_options = [opt.strip() for opt in options]
        if len(set(stripped_options)) != len(stripped_options):
            raise ValueError("Варианты ответов должны быть уникальными")

        self.question = question.strip()
        self.options = stripped_options
        self.votes = {opt: 0 for opt in self.options}
        self.voters = set() 

    def vote(self, user_id: str, choice: str) -> bool:
        "Голосование. Возвращает True если голос принят."
        if user_id in self.voters:
            return False
        if choice not in self.votes:
            return False
        self.votes[choice] += 1
        self.voters.add(user_id)
        return True

    def get_results(self) -> dict:
        return self.votes.copy()

    def total_votes(self) -> int:
        return sum(self.votes.values())

    def has_voted(self, user_id: str) -> bool:
        return user_id in self.voters


class VotingSystem:
    def __init__(self):
        self.polls = {}   
        self.next_poll_id = 1

    def create_poll(self, question: str, options: list[str]) -> int:
        poll = Poll(question, options)
        poll_id = self.next_poll_id
        self.polls[poll_id] = poll
        self.next_poll_id += 1
        return poll_id

    def vote(self, poll_id: int, user_id: str, choice: str) -> bool:
        if poll_id not in self.polls:
            return False
        return self.polls[poll_id].vote(user_id, choice)

    def get_poll_results(self, poll_id: int) -> dict | None:
        if poll_id not in self.polls:
            return None
        return self.polls[poll_id].get_results()

    def get_total_votes(self, poll_id: int) -> int | None:
        if poll_id not in self.polls:
            return None
        return self.polls[poll_id].total_votes()

    def list_polls(self) -> list[dict]:
        return [
            {"id": pid, "question": poll.question}
            for pid, poll in self.polls.items()
        ]