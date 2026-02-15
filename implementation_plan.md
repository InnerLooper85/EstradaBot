# EstradaBot — Implementation Status

**Last Updated:** February 15, 2026
**Current Product Version:** MVP 1.7
**Next Milestone:** MVP 1.8 (then MVP 2.0)

> Full original plan (with detailed phase specs and code examples) archived to `archive/implementation_plan_v1.md`.

---

## Phase Status Summary

| Phase | Focus | Status | Notes |
|-------|-------|--------|-------|
| Phase 1: Data Foundation | Parsers, validation | COMPLETE | All parsers implemented |
| Phase 2: Core Scheduling | DES engine | COMPLETE | Pipeline-based DES in `des_scheduler.py` |
| Phase 3: Optimization | Priority, hot list, rubber | MOSTLY COMPLETE | Rubber grouping not done (LOW priority) |
| Phase 4: User Interface | Flask web app | COMPLETE | Bootstrap 5, jQuery, DataTables |
| Phase 5: Visual Simulation | Factory floor animation | COMPLETE | Canvas-based, `simulation.js` |
| Phase 6: Reporting & Export | Excel reports | MOSTLY COMPLETE | Utilization + alert reports not done |
| Phase 7: Testing | Automated tests | IN PROGRESS | Manual testing only, no pytest yet |
| Phase 8: MVP 1.1 Feedback | 11 user feedback items | COMPLETE | All 11 items done in one session |
| Deployment | Cloud Run + GCS | COMPLETE | Live at estradabot.biz |

---

## Version History

| Version | Date | Key Changes |
|---------|------|-------------|
| MVP 1.0 | Feb 1, 2026 | Initial release — DES engine, web app, simulation, reports |
| MVP 1.1 | Feb 4, 2026 | User feedback: BLAST time fix, rubber alternation, serial number, column filters, version header, feedback form, data scrubbing, schedule mode toggle, published schedule concept |
| MVP 1.2 | Feb 4, 2026 | Bug fixes from 1.1 deployment |
| MVP 1.3 | Feb 7, 2026 | Planner workflow: 3-scenario simulation, scenario comparison, base schedule selection, publish flow |
| MVP 1.4 | Feb 10, 2026 | Special Requests page, Mode A/B, approval queue, impact preview, reconciliation |
| MVP 1.5 | Feb 12, 2026 | Mfg Eng Review page, DCP Report parser |
| MVP 1.6 | Feb 13, 2026 | Bug fixes: role case sensitivity, file name detection (OSO/SDR patterns) |
| MVP 1.7 | Feb 14, 2026 | Order holds, special instructions column, simulation defaults to published schedule, DCP parser, feedback status tracking, notification bell, alert reports |

---

## MVP 1.x Backlog

Items moved from the original MVP 2.0 plan to 1.x during roadmap replanning (Feb 15, 2026):

| Item | Priority | Status | Notes |
|------|----------|--------|-------|
| Resource utilization report | MEDIUM | Not started | MVP 1.8 target |
| Role name normalization | MEDIUM | Not started | Fix `customer_service` vs `customerservice` |
| Extended simulation (6-day, skeleton shifts) | HIGH | Not started | Skeleton = takt time adjustment |
| RBAC / user management | MEDIUM | Not started | Role matrix deferred |
| Core Mapping: read-only web view | MEDIUM | Not started | Precursor to 2.0 editable database |
| Days Idle column | MEDIUM | Not started | From Shop Dispatch "Elapsed Days"; 9999→0 |
| Basic schedule reorder | MEDIUM | Not started | Simple priority adjustment |
| Rubber grouping optimization | LOW | Not started | Changeover minimization |
| Automated unit tests (pytest) | MEDIUM | Not started | |
| Automated integration tests | MEDIUM | Not started | |

---

## MVP 2.0 Planning

See `MVP_2.0_Planning.md` for full details. **Scope redefined Feb 15, 2026.** Key features:

1. **Rotors product line** — second department with own staffing, machines, scheduling logic
2. **Customer-facing reports & quoting system** — customer reports, quotes with temporary capacity holds
3. **Full schedule manipulation GUI** — drag-drop reorder, resource reassignment
4. **Core Mapping editable database** — replace Excel upload with web editor
