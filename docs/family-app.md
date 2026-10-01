# The family app (planned, nothing built yet)

The door is not meant to be configured through YAML files forever. The plan is a small,
self-hosted web app that the household uses day to day, while Home Assistant stays the
automation hub underneath.

## What it should do

- **Screen notices:** put a message on the door's e-paper screen ("Back in 20 minutes",
  "Parcels please to the neighbours"), with an expiry time.
- **Chimes:** choose the ringtone that plays on the speakers inside the house, and its volume,
  per room and per time of day.
- **Silence:** a quiet mode that routes rings to a quiet notification channel.
- **Other home systems and speakers:** one interface instead of several apps.
- **Talk (later):** could host the relay for live push-to-talk from the door into the house.

## How it connects

```
 household (browser / phone) ──► family app ◄──► Home Assistant ◄──► door computers (ESPHome)
                                      ▲                 │
                                      └── status & ─────┘
                                          control API
```

- The app exposes an **API and a Home Assistant integration**, so every setting it owns is also
  visible to automations (status and control).
- The door firmware keeps its settings reachable over ESPHome entities and services instead of
  burying them in firmware. That is a constraint on the firmware today, even though the app
  comes later.
- Self-hosted, no cloud dependency; accounts only for the household.

## Open questions

- Framework and hosting (it will run next to Home Assistant on the home server).
- Whether the push-to-talk relay lives in the app or in Home Assistant.
- How screen notices avoid telling strangers that nobody is home.
