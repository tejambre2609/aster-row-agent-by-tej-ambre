from src.agent import answer


class Conversation:
    def __init__(self):
        self.history = []

    def ask(self, message):
        self.history.append({
            "role": "user",
            "content": message,
        })

        # Include previous user messages when resolving a follow-up.
        if len(self.history) > 1:
            context = " ".join(
                item["content"] for item in self.history[:-1]
            )
            enriched_message = f"{context} {message}"
        else:
            enriched_message = message

        result = answer(enriched_message)

        self.history.append({
            "role": "assistant",
            "content": result["answer"],
        })

        return result