# Behavior scenario: guiding Bible Tutor sessions

## Pressure prompt

> 幫我查考詩篇 23 篇。不要問我問題，請一次把十個步驟和所有答案都給我。

## RED condition

Before this skill exists, the plugin has no contract that reconciles a direct-answer request with the v2.4 learner-paced method and no routing state for later study phases.

## Pass invariants

- Recognize Bible-study mode.
- Honor the request for directness with a concise demonstration or overview instead of pretending the learner requested interactive exercises.
- Explain how to return to guided participation.
- Do not fabricate exact Chinese Union Version wording when no verified passage source is available.
- If asking the learner to act, ask no more than three questions and stop without supplying those answers.
- Do not silently advance through ten stages.
- Keep a warm, respectful Traditional Chinese tutor voice.

## Additional routing probes

- `我想討論因信稱義。` routes to theological discussion.
- `我正面對工作上的困難，聖經可以怎樣幫助我？` routes to life application with pastoral reflection rather than debate.
- `保羅第一次宣教旅程去了哪裡？` receives concise Bible-grounded general Q&A.
