/* Renders an agent result (from triage/serialize.py) as a triage tag plus detail panels.
   Shared by the live demo (web/demo.html) and the showcase page (docs/index.html). */
(function () {
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const RULES = {
    several_people: "several people are affected",
    customers_waiting: "customers are waiting",
    cannot_work: "the person can't work at all",
  };

  function reviewReasons(d) {
    const reasons = [];
    if (d.kb && d.kb.needs_review) reasons.push(d.kb.review_note);
    (d.reply_problems || []).forEach((p) => reasons.push("The draft reply " + p + "."));
    return reasons;
  }

  function tag(d, opts = {}) {
    const t = d.triage;
    const p = (t.priority || "").toLowerCase();
    const raised = t.raise_check === "accepted";
    const why = raised ? `Raised from ${t.default_priority}: ${RULES[t.raise_rule] || t.raise_rule}`
                       : `Normal priority for ${t.subcategory}`;
    const reasons = reviewReasons(d);
    const flag = reasons.length
      ? `<p class="tag__flag"><strong>Check before sending.</strong> ${esc(reasons[0])}</p>` : "";
    const kb = d.kb ? `<div><dt>KB article</dt><dd>${esc(d.kb.primary.id)} ${esc(d.kb.primary.title)}</dd></div>` : "";
    return `<div class="tag-wrap">
      <article class="tag tag--${esc(p)}" aria-label="Triage result: ${esc(t.subcategory)}, ${esc(t.priority)} priority">
        <div class="tag__body">
          <p class="tag__id">${esc(d.ticket.ticket_id)}</p>
          <h3 class="tag__sub">${esc(t.subcategory)}</h3>
          <p class="tag__cat">${esc(t.category)}</p>
          <dl>
            ${kb}
            <div><dt>From</dt><dd>${esc(d.ticket.requester)}, ${esc(d.ticket.role)}, ${esc(d.ticket.location)}</dd></div>
          </dl>
          ${opts.noFlag ? "" : flag}
        </div>
        <div class="tag__strip"><span class="p">${esc(t.priority)}</span><span class="why">${esc(why)}</span></div>
      </article></div>`;
  }

  function steps(d) {
    const t = d.triage;
    let raise;
    if (!t.raise_rule || t.raise_rule === "none") {
      raise = "The AI found no sign of wider impact, so the normal priority stands.";
    } else {
      const claim = `The AI said ${esc(RULES[t.raise_rule] || t.raise_rule)} and quoted <q>${esc(t.evidence)}</q>.`;
      if (t.raise_check === "accepted") {
        raise = `${claim} <span class="ok">Accepted:</span> the quote is in the ticket and shows wider impact, so priority goes up one level.`;
      } else if ((t.raise_check || "").includes("not in ticket")) {
        raise = `${claim} <span class="no">Rejected:</span> those words aren't in the ticket.`;
      } else {
        raise = `${claim} <span class="no">Rejected:</span> the quote doesn't show wider impact.`;
      }
    }
    return `
      <ol class="steps">
        <li><span>The AI read the ticket: <strong>${esc(t.subcategory)}</strong>. <span class="muted">${esc(t.reason)}</span></span></li>
        <li><span>The code looked up the normal priority for ${esc(t.subcategory)}: <strong>${esc(t.default_priority)}</strong>.</span></li>
        <li><span>${raise}</span></li>
        <li><span>Final priority: <strong>${esc(t.priority)}</strong>.</span></li>
      </ol>`;
  }

  function kbList(d) {
    if (!d.kb) return "";
    const rows = [`<li><span class="id">${esc(d.kb.primary.id)}</span><span class="used">${esc(d.kb.primary.title)}</span><span class="score">used for the reply</span></li>`];
    d.kb.related.forEach((a) => rows.push(
      `<li><span class="id">${esc(a.id)}</span><span>${esc(a.title)}</span><span class="score">${Math.round(a.score * 100)}% similar</span></li>`));
    return `<ul class="kb-list">${rows.join("")}</ul>`;
  }

  function detail(d, opts = {}) {
    if (!d.triage.ok) {
      return `<p class="status error">The classifier couldn't produce a valid answer: ${esc(d.triage.error)}</p>`;
    }
    // The tag already shows the first review reason; list only the reply's own problems here.
    const replyProblems = (d.reply_problems || []).map((p) => "The draft reply " + p + ".");
    const problems = replyProblems.length
      ? `<ul class="problems">${replyProblems.map((r) => `<li>${esc(r)}</li>`).join("")}</ul>` : "";
    let expected = "";
    if (d.expected) {
      const right = d.expected.subcategory === d.triage.subcategory && d.expected.priority === d.triage.priority;
      expected = `<p class="expected">${right ? '<span class="ok">Matches</span>' : '<span class="no">Differs from</span>'} the correct answer in the dataset: ${esc(d.expected.subcategory)}, ${esc(d.expected.priority)}.</p>`;
    }
    const models = d.models.classifier === d.models.reply
      ? `${esc(d.models.classifier)}` : `${esc(d.models.classifier)} classified, ${esc(d.models.reply)} wrote the reply`;
    return `
      <div class="detail">
        <div>${tag(d)}${expected}</div>
        <div class="detail__panels">
          <div class="panel"><h3>How the priority was set</h3>${steps(d)}</div>
          <div class="panel"><h3>Knowledge base</h3>${kbList(d)}</div>
          <div class="panel"><h3>Draft reply for the agent to review</h3><pre class="letter">${esc(d.reply)}</pre>${problems}</div>
          <p class="meta">Models: ${models}. Took ${Number(d.latency_s).toFixed(1)} seconds.</p>
        </div>
      </div>`;
  }

  function rawTicket(tk) {
    return `
      <div class="raw-ticket">
        <p class="from">${esc(tk.ticket_id)} from ${esc(tk.requester)}, ${esc(tk.location)}</p>
        <p class="subject">${esc(tk.subject)}</p>
        <p class="body">${esc(tk.description)}</p>
      </div>`;
  }

  window.Triage = { esc, tag, detail, rawTicket };
})();
