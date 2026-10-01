# Building an AI help desk triage agent: what worked, what didn't, and why

## The problem

Most IT help desk tickets are repetitive: password resets, printers, Outlook, Wi-Fi. Before anyone can fix them, someone has to read each one, decide what kind of problem it is, decide how urgent it is, find the right knowledge base article if technician does not know how to fix the issue, and write a first reply. That first pass is where time goes, and where urgent tickets get missed when a store's card reader failure is buried in a ticket titled "Issue."

I wanted to see how much of that first pass an AI agent could handle reliably, using only free models running on a laptop.

## What I built

The agent takes a ticket as an employee wrote it and returns:

1. **The problem type and priority**, with a traceable explanation of how the priority was set
2. **The knowledge base article** to use, plus related articles found by meaning-based search
3. **A draft reply** for a human agent to review, written only from that article's steps
4. **A review flag** when something looks off, such as the classification and the search disagreeing

Everything runs locally through Ollama (Qwen 2.5 7B, Llama 3.2 3B, and nomic-embed-text for embeddings). All tickets are synthetic, generated with realistic noise: vague subjects, typos, all-lowercase text, two problems in one ticket, and impact statements buried at the end. Each noisy ticket is tagged so accuracy can be reported separately on clean and messy tickets.

## How I measured it

The dataset has 2,800 practice tickets for development and 200 held-out tickets used only for scoring. After four rounds of improvements based on that evaluation set, I generated a fresh set of 200 tickets that no version had seen, and report that as the final score.

For the replies, I used rule-based safety checks (no password requests, no invented links or phone numbers, no internal labels) plus an AI judge that grades whether each reply stays grounded in the knowledge base article and whether its steps fit the problem.

## What changed, and why

| Version | Model | Fully correct | What changed |
|---|---|---|---|
| v1 | Llama 3B | 59.0% | First prompt |
| v2 | Llama 3B | 83.0% | Default priority per problem type, explicit raise rules |
| v3 | Llama 3B | 69.5% | AI quotes evidence, code sets priority |
| v3 | Qwen 7B | 89.0% | Same design, larger model |
| v4 | Llama 3B | 94.5% | Code also checks the evidence fits the rule |
| v4 | Qwen 7B | 98.0% | Best on the tuning set |
| **Final** | **Qwen 7B** | **97.0%** | **Fresh, unseen tickets** |

"Fully correct" means both the problem type and the priority match.

**v1 to v2.** The first version classified problems well but over-prioritized badly, setting 58 of 200 tickets too high. Its own explanations showed why: it raised priority because "the issue has been ongoing for a week" or because the ticket came from a store, neither of which was a rule. Giving each problem type a default priority, like an SLA matrix, and listing what does and doesn't justify a raise took fully correct from 59% to 83%.

**v2 to v3.** The remaining errors were invented impact: "the whole store is affected" for a single frozen register. So I stopped letting the AI choose the priority at all. It now reports which raise rule applies and quotes the words from the ticket that prove it, and code calculates the priority, rejecting any quote that isn't actually in the ticket. A simulation with perfect AI answers reproduced all 200 correct priorities, which proved the rules in code were complete.

**The surprise.** v3 made the larger model better (89%) and the smaller model worse (69.5%). The small model learned to claim "several people affected" while quoting any real sentence, like "My account got locked about an hour ago." The check confirmed the quote existed, not that it proved anything. The same design helped one model and hurt another.

**v3 to v4.** A second check now requires the quote to actually show wider impact, such as mentioning several people or customers. The small model recovered to 94.5%, and Qwen reached 98%. On the fresh set, Qwen scored 97%, close enough to suggest the rules generalized rather than memorizing the evaluation tickets.

## The full agent

Adding knowledge base search and reply drafting produced a different set of lessons.

**The review flag works.** The KB search runs independently from the ticket text, so when it disagrees with the classifier, the ticket is flagged for a human. With the small model classifying, it caught all 3 classification mistakes in 60 tickets, with 3 false alarms.

**The AI judge was wrong more often than the replies.** In one run, the judge said only 63% of replies were grounded in the knowledge base. When I made the judge quote the sentence it considered invented and had code check that quote against the article, 10 of its 11 flags turned out to quote text that was in the article. The real figure was about 97%. Without verifying the judge, I would have reported a badly wrong number.

**Small models copy.** Llama pasted the one example sentence from my reply instructions ("we'll re-add the printer for you") into Outlook and Wi-Fi replies, just as it had copied an example's reasoning word for word in v1. Removing example sentences from instructions fixed it.

**Splitting the work saves time.** Using the small model to classify and the larger one to write cut the average time per ticket by about 32%, with the same reply quality and the review flag covering the small model's mistakes.

**The knowledge base sets the ceiling.** A scan-to-email ticket got printing steps because the article only covered printing; the reply was perfectly grounded and completely unhelpful. Labeling each article's steps by situation ("Printing:", "Scan to email:") worked better than any prompt instruction. As an ITSM administrator, this matched what I see daily: the quality of self-service depends on the quality of the knowledge base.

## Lessons

- **Let code apply the business rules.** The AI is good at reading messy text; deterministic rules belong in code, where they can be tested and proven.
- **Make the AI show its work, and verify it.** Every claim that changes an outcome, whether an escalation or a judge's grade, comes with a quote the code checks.
- **Test design choices on more than one model.** A change that helps a larger model can hurt a smaller one.
- **Know when to stop tuning.** Once the fresh test set's results were in, I documented the remaining failure modes instead of fixing them, so the 97% stays an honest measurement.

## Limitations

- The tickets are synthetic and template-based, so real tickets would be harder. The phrase lists that confirm escalation evidence were written with this dataset's wording in view.
- The checks that stop invented escalations occasionally block real ones: 5 of the 6 misses on the fresh set were escalations the AI understood correctly but phrased differently than the ticket, or labeled with the wrong rule name. That pushes errors toward under-prioritizing, the costlier direction in a help desk.
- The knowledge base has one article per problem type, so the search's real value would show more in a large, overlapping knowledge base.
- The AI judge itself has not been measured against human grades.

## What I'd do next

- Grade a small set of replies by hand and measure how often the AI judge agrees
- Accept escalation quotes that fit any raise rule, and test on a new unseen set
- Connect the agent to a Freshservice sandbox through a webhook, writing the classification to ticket fields and the draft as a private note
