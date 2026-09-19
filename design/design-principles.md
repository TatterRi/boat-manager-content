# Boat Manager — design principles

Why the data model is shaped the way it is, what that commits us to, and where the
code currently departs from it.

Written 19 September 2026 against the app repo at `46008ca` (1.5.0). This is a
reference note, not a proposal: it records decisions already taken, names the one
that was taken by accident, and gives a rule new work can be checked against.

---

## 1. Two origins

**It started as a spreadsheet.** Many sheets, imported. That is why the schema is
wide — one column per cost category rather than a row per transaction — why CSV
import and export are first-class rather than an afterthought, and why an owner
arriving with their own spreadsheet is on the expected path rather than a fringe
one.

**The day log stands alone.** Not a legal document, but close enough that it is
treated as one: a log entry says what happened on a day, and nothing changes it
except the owner explicitly editing it. Equipment maintenance is the one
deliberate exception — fully relational, because nothing else worked.

Both are good reasons. Neither is written anywhere a user can read, which is a
separate problem and is tracked as its own piece of work.

---

## 2. What "stands alone" protects, and what it does not

The guarantee is about **the words**. A log entry's text is the owner's record of
their day. Re-reading a 2019 log must show what it showed in 2019, whatever has
been renamed, deleted or reorganised since.

The guarantee is **not** an argument against references. Those are two different
properties:

| Property | What it means | How you get it |
| --- | --- | --- |
| **Immutability** | The record's content does not change behind the owner's back | Store the words. Write once, read back verbatim. |
| **Referential integrity** | The app can still find what a record refers to | Store a stable, meaningless handle alongside the words |

They are orthogonal. You can have both, and the app already does in two places.

---

## 3. The rule

> **A log entry stores what happened, in words the owner owns, plus an opaque
> handle for finding things again. The words are the record. The handle is never
> shown, never edited, and never load-bearing for what the entry says.**

Corollaries:

- **A name is a label, not a key.** Identity is carried by something stable and
  meaningless. The moment a key carries meaning, editing the meaning breaks the key.
- **Auto-fill is a one-time bargain.** Anything the app fetches on the owner's
  behalf is written into the entry once and read back verbatim thereafter. It is
  never re-derived on display.
- **Nothing rewrites an entry but the owner.** Where the app believes a record is
  wrong, it says so and proposes a fix. It does not apply one.

---

## 4. Where the rule is already applied

**Tides (1.5.0).** The log stores `tides` — the editable summary line the master
owns — and separately `tideStation`, `tideStationID` ("NOAA id, for re-deriving
later if ever needed"), `tideDatum`, `tideUnit`, `tideTimeZone` and
`tideEventsJSON`. All written once when the entry is filled in, read back verbatim
thereafter. The PDF prints the recorded line and looks nothing up. This is
snapshot-plus-handle, built deliberately.

**Weather.** The same bargain, and the code says so —
`LogTideSubView.swift:7`: *"auto-filled and then editable — the same bargain as the
weather."* `weather`, `weatherSF` and `wind` are stored on the `Log`.

**The maintenance summary.** `log.maintenanceTask` is a stored summary string
alongside the live relationship. `ListLogPDFView:184-188` prints that string and
falls back to a live count of the relationship only when it is empty — so a
historical log prints its own snapshot, not a recomputation.

**Data Health (1.5.0).** Reads the logs for what cannot be right, says why it
matters, proposes the fix, and changes nothing until the owner taps Fix. This is
the rule expressed as a feature, and it is the pattern any future repair should
take.

---

## 5. Where the code departs from it

### 5.1 Names used as keys

The upkeep dashboard resolves a logged task to a piece of equipment by exact,
lowercased string equality:

- `Shared/UpkeepStatus.swift:259` — the task's name must equal an item's name
- `UpkeepStatus.swift:261, 273` — `MaintenanceTasks.maintenanceEquip` is a
  **comma-separated string of equipment names**, split and lowercased
- `Shared/CoreData/CDFunctions.swift:353-372` — `autoLinkMaintenanceItems` links by
  `equipType` string equality

This is the accidental decision. It does not follow from the standalone-log rule —
it is the rule's mechanism (store words) applied to a job the rule never asked it
to do (establish identity).

Consequences, all silent:

- Rename a piece of equipment and its maintenance history detaches. Nothing errors.
- "Hull Zincs" never matches an item named "Zincs — Hull".
- A comma inside an equipment name splits one entry into two phantom ones.
- A failed match renders as **"No logs available"** — indistinguishable from "this
  job has never been done", which is the opposite of the truth.

The cost lands where it hurts most: the log's *words* survive, but the *knowledge*
connecting them does not. Every feature that queries across records — the upkeep
dashboard, cost per engine hour, cost of ownership — sits on that matching.

**The fix is snapshot-plus-handle, applied here too:** a write-once `equipID` on
`MaintenanceTasks`, used for resolution only, with the existing name match kept as
a permanent fallback; written on an explicit save; legacy rows surfaced as a Data
Health finding rather than a background repair. No migration, no writes to `Log`.

### 5.2 Two launch passes rewrite logs

Both shipped, both write to `Log` with no user action:

- `CDFunctions.swift:298-311` — `backfillMaintenanceTaskSummaries` writes
  `log.maintenanceTask`, a field that is displayed, filtered on and printed.
- `CDFunctions.swift:321-334` — `repairNegativeLogHours` writes `hrsUnderway`,
  `hrsEngine`, `hrsGenSet` on logs whose elapsed hours went negative.

Both are defensible repairs. `repairNegativeLogHours` is idempotent, documented as
safe on every launch and on every synced device, and fixes data that was arithmetic
nonsense. But the rule says nothing rewrites an entry but the owner, and these do.

Either the rule has two named exceptions — written down, with the reasoning — or
they become Data Health findings like everything else. Leaving it implicit is the
only wrong answer, because it makes the rule unenforceable for the next case.

---

## 6. Alternatives considered

**Full normalisation.** Rejected. It does not serve the standalone-log goal, it
breaks the spreadsheet import path that is how owners arrive, and it is a large
migration for a benefit that snapshot-plus-handle delivers at a fraction of the
cost.

**Append-only corrections.** A correction never overwrites; it appends a new record
with a reason, and nothing is ever destroyed — how a paper log actually works, where
an error is struck through and initialled rather than erased. This is *stronger*
than the current design, which rewrites in place in the two cases above. Deferred:
every read becomes "latest non-superseded", and the UI has to show history. Revisit
only if the log is ever meant to carry evidentiary weight.

**Status quo.** Defensible for a logbook. Not defensible for an app with a
maintenance dashboard, an analysis section and a cost-of-ownership ambition — those
are queries across records, and they need identity to be reliable.

---

## 7. Checking new work against the rule

Four questions for anything that touches a log or a maintenance record:

1. **Does it write to a record the owner did not just edit?** If yes, it is a Data
   Health finding, not a write.
2. **Does it establish identity with something the owner can rename?** If yes, add a
   handle and keep the name for display.
3. **Does it re-derive on display something that was auto-filled earlier?** If yes,
   store the snapshot instead. The log shows what it showed.
4. **Would a rename, a deletion or a reorganisation change what an old entry says?**
   It must not.

---

## 8. Consequences accepted

The wide schema cannot grow without a migration — every new cost category is a
schema change. That is the known price of the spreadsheet origin, it is the central
complaint in the expenses feature spec, and it is a separate decision from anything
in this note. Snapshot-plus-handle does not fix it and does not make it worse.
