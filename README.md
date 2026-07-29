# 📊 Editorial Developer CRM

CRM für die von **Dominik Hoferer** betreuten EU-Apps-Developer.
Enthält Stammdaten (Business Manager, EAM Category, Attention Level, Top-100-Märkte, EU-Billings/YoY),
90-Tage-Performance mit Peak-Erkennung sowie **IAE (In-App Events)** und **Nominations (Roadmaps)**,
die per Knopfdruck über GitHub Actions aus der internen Huxley-API nachgeladen werden.

## 🖥️ Live ansehen

Entweder lokal öffnen (`index.html` im Browser) oder via **GitHub Pages** deployen:

1. Repo-Settings → Pages → Source: `main` Branch, Root-Verzeichnis
2. Seite ist dann unter `https://<user>.github.io/<repo>/` erreichbar

## 🔄 IAE & Nominations aktualisieren ("Knopfdruck")

1. GitHub Repo → Tab **Actions**
2. Workflow **„Refresh IAE & Nominations“** auswählen
3. **„Run workflow“** klicken (optional Storefront-ID angeben, Default `143443` = Deutschland)

Der Workflow ruft für jede App in `data/developers.json` folgende Huxley-Endpunkte ab:

- Nominations: `https://huxley.itunes.apple.com/v2/detail/{adamId}/{storefront}/iap/roadmaps`
- IAE: `https://huxley.itunes.apple.com/v2/detail/{adamId}/{storefront}/iap/events`

Ergebnisse werden in `data/nominations.json` bzw. `data/iae.json` geschrieben und automatisch committed.
Zusätzlich läuft der Workflow täglich um 05:00 UTC automatisch.

> Hinweis: Der Fetch benötigt Netzwerkzugriff auf `huxley.itunes.apple.com` (Apple-intern/VPN).
> Läuft der Workflow außerhalb des internen Netzes, schlägt der Request fehl — die JSON-Dateien
> enthalten dann `{"error": ...}` pro App.

## 📁 Struktur

```
index.html                        # Single-Page CRM (Chart.js, kein Build nötig)
data/developers.json               # Stammdaten aller betreuten Developer/Apps
data/performance_series.json       # Tägliche EU-Billings je App (12 Monate)
data/performance_dates.json        # Zugehörige Datumsachse
data/performance_peaks.json        # Vorab berechnete Peak-Werte + Peak-Datum je App
data/nominations.json              # Von der Huxley-API geladene Nominations (Roadmaps)
data/iae.json                      # Von der Huxley-API geladene In-App Events
scripts/fetch_editorial_data.py    # Fetch-Skript, das der Workflow ausführt
.github/workflows/refresh-data.yml # GitHub Action für den "Knopfdruck"-Refresh
```

## 📈 Aktuelle Performance-Peaks (Stand: 12-Monats-Export)

| App | Peak-Datum | Peak-Wert |
|---|---|---|
| AI Calorie Tracker by Yazio | 05.01.2026 | $622.286 |
| WOW | 28.02.2026 | $197.236 |
| Babbel - Language Learning | 04.01.2026 | $131.858 |
| MEGOGO: TV, Movies, Audiobooks | 19.07.2026 | $131.419 |
| Joyn \| deine Streaming App | 28.02.2026 | $109.734 |
| Napper: Baby Sleep Tracker | 23.06.2026 | $55.457 |
| Instories: AI Photo & Video | 11.02.2026 | $36.144 |
| Finary: Budget & Money Tracker | 10.01.2026 | $33.416 |
| Astra AI: Study & Exam Prep | 18.05.2026 | $30.393 |
| Yuno - General knowledge | 19.07.2026 | $16.232 |
| Emma: Learn Languages | 22.12.2025 | $11.822 |
| Ivy: Processed Food Scanner | 27.02.2026 | $11.575 |
| Instinct: Casual Dating App | 02.11.2025 | $8.569 |
| Jodel: Hyperlocal Community | 28.02.2026 | $3.016 |

*(ChatOn AI, Blinkist, calimoto und Splash sind in den Stammdaten aber nicht im Billings-Export enthalten — Performance-Peak daher `—`.)*
