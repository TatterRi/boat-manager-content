# Why the description changed

Notes on the edits in `description.md`, checked against the app source
rather than guessed.

## Factual corrections

**Mac was missing.** `SUPPORTS_MACCATALYST = YES` in the project, and
boatmanager.app already carries a Mac App Store badge. The old opening
said "on your iPad and iPhone", which undersells the app and contradicts
the store listing. Every device mention now reads iPhone, iPad and Mac.

**Planning, Projects and batch scheduling were absent.** They shipped in
1.4.3 and are the largest additions in a year, but the description had
only "Maintenance Dashboard". The description is not versioned — it
should describe the app as it stands today, not as it stood two releases
ago.

**Hours-based reminders were absent.** Service intervals are now dated
from logged engine readings rather than a flat monthly figure. That is a
real differentiator against calendar-only maintenance apps.

**Apple Weather was buried.** WeatherKit is integrated into both the
logbook and the Helm; it appeared as a single word inside one Helm
bullet. It now appears where it is used. (Apple requires the in-app
attribution that `DataAttributionView` already provides.)

## Subscription disclosure

The old line — "A subscription is required thereafter, for a small fee" —
is a rejection risk under guideline 3.1.2, which wants the price and the
duration stated. It also hides good news: at $0.99/month or $9.99/year
the price is a selling point, not something to apologise for. Both tiers
are confirmed against App Store Connect.

One thing left over: the description says the first 30 days are free,
while the in-app help (`help.json`, "Is the application free of
charge?") still says "free for the first month". Same intent, two
wordings, and the store listing is the one a prospective buyer reads
first. Worth making the help match.

## Structure

The first two or three lines are all anyone sees before tapping "more",
and the old opener simply restated the app's name. It now leads on what
the app does, followed by the Master Mariner and Royal Navy line from the
in-app About text — the strongest credibility hook available, and it was
nowhere in the listing.

Fourteen sections became eleven. Administrative and Document Storage
carried the identical "Expiry dates with optional Apple Calendar
reminders" bullet and were merged; Analysis and PDF Reports were merged;
Apple Reminders folded into an ecosystem section with Calendar, Contacts,
Weather and iCloud. Sections are ordered by what distinguishes the app,
since few readers reach the bottom.

## Small fixes

- "Build in Analysis & Graphs" → "Built-in"
- "Link spares to each equipment" → "to the equipment they fit"
- "Cost, Fuel, Tankage and Emissions" had no verb; folded into the
  statistics bullet
- Trailing space after "Equipment History"
- Tabs before each bullet removed — App Store Connect renders plain text
  and tabs can come out ragged
- Fuel-consumption curve added; it is in the in-app About text but was
  not in the listing

## The safety disclaimer

Included, and confirmed to stay:

> Note: the emergency and float-plan features are aids, not a substitute
> for a VHF/DSC radio, an EPIRB, or leaving a float plan with someone
> ashore.

It sits after the subscription line, at the foot of the listing, where it
qualifies the emergency and float-plan claims without interrupting the
read. To the audience this app is written for it reads as competence
rather than hedging — the people who care about a CG-719S summary are the
same people who would notice its absence.

## Worth knowing

The description does not feed App Store search. Only the app name,
subtitle and the 100-character keyword field are indexed, so there is no
reason to write the description for keywords — it should be written to
convert someone already looking at the page.
