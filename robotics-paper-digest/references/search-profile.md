# Search and Screening Profile

## Sources

Use sources in this order:

1. official proceedings or publisher record;
2. arXiv abstract and HTML/PDF;
3. official author project page and repository;
4. institutional news or company blog, labeled as non-paper evidence.

The bundled daily job searches arXiv `cs.RO`. It uses the Atom API when available and the official category RSS feed
when shared CI IPs are rate-limited. The RSS feed is a current announcement batch, so after a multi-day automation
outage, run an explicit API/manual backfill instead of assuming the RSS fallback covered the full lookback window. For
deeper manual research, also inspect relevant official venue pages for RSS, ICRA, IROS, CoRL, Humanoids, RA-L, T-RO
and Science Robotics. Cross-listed `cs.AI`, `cs.CV` and `cs.LG` papers should enter only when the paper itself is
materially about robots.

## Ranking

Rank by research relevance, not title novelty. The default profile prioritizes:

- humanoid and biped platforms;
- legged locomotion and loco-manipulation;
- whole-body control, contact and foothold safety;
- reinforcement/imitation learning and sim-to-real;
- depth/RGB-D perception, terrain representations and world models;
- manipulation, VLA systems and teleoperation when they affect embodied control.

Keep broad `cs.RO` coverage so the digest can surface unexpected methods. A low keyword score is a ranking signal, not proof of irrelevance.

## Evidence Labels

- `peer-reviewed`: confirmed through proceedings or publisher;
- `accepted`: acceptance is explicitly stated by a reliable primary source, publication pending;
- `preprint`: arXiv without independently verified venue;
- `demo`: project/company material without a paper;
- `inference`: analyst conclusion derived from cited facts.
