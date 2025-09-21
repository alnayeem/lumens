Lumens Community (MVP scaffold)

Overview
- Open, multi-community catalog of public media (videos, podcasts) with transparent policies.
- This repo starts with the core data model, policy stub, and a seed channel list.

What’s here
- Proto schema: `proto/lumens/v1/media.proto` (canonical MVP entities)
- Policy stub: `policies/islamic_commons/kids/policy.yaml`
- Policy schema: `tools/policy_schema.json`
- Seed channels: `data/channels/islamic_kids.csv`
- Ingest CLI: `services/ingest/yt_ingest.py` (fetch latest YT videos)

IDs & conventions
- Community: slug (e.g., `islamic_commons`)
- Vertical: `{community}/{vertical}` (e.g., `islamic_commons/kids`)
- Channel: `yt:{UCID}` (prefix by source)
- Content: `yt:{VIDEOID}`
- PolicyDoc: `{scope}/{name}@{version}`

Firestore layout (initial)
- `communities/{communityId}` → `name`, `default_org_id`, `policy_doc_id`, `enabled_vertical_ids[]`
- `verticals/{communityId}_{verticalId}` → `name`, `status`, `policy_doc_id`, `restrictions{age_bands[], regions_allowed[], acceptable_topics[]}`, `channel_ids[]`
- `channels/{channelId}` → `creator_id`, `organization_id?`, `source`, `source_ref`, `title`, `status`
- `communityChannels/{communityId}_{channelId}` → `community_id`, `channel_id`
- `content/{contentId}` → `channel_id`, `source_item_id`, `title`, `published_at`, `duration_seconds`, `languages[]`, `regions[]`, `topics[]`, `age_rating{}`, `thumbnails[]`, `provenance{}`, `signals{}`
- `policies/{scope}_{id}_{version}` → `scope`, `version`, `rules` (compiled JSON), `created_at`

Indexes (suggested)
- `content`: `channel_id ASC, published_at DESC`
- `content`: `topics ARRAY_CONTAINS, published_at DESC`
- `verticals`: `status ASC, community_id ASC`

Local Ingest (dev)
- Create `.env` at repo root with your YouTube API key:
  - `echo 'LUMENS_YT_API_KEY=YOUR_KEY' > .env`
- Run via module (preferred) or legacy path:
  - `python -m services.ingest.cli --channels data/channels/islamic_kids.csv --out out/islamic_kids --limit 100`
  - `python services/ingest/yt_ingest.py --channels data/channels/islamic_kids.csv --out out/islamic_kids --limit 100`
- Or use Makefile shortcuts (with defaults):
  - `make ingest LIMIT=25`
  - `make ingest-no-enrich LIMIT=25`
- Optimize quota usage:
  - Resolve channels once and cache mapping:
    - `make resolve-channels CHANNELS=data/channels/islamic_kids.csv CHANNELS_MAP=out/channels_map.json`
  - Then ingest using cached map and incremental state:
    - `make ingest-cached LIMIT=25 CHANNELS_MAP=out/channels_map.json STATE=out/state.json`
- Outputs (git-ignored):
  - `out/islamic_kids.ndjson` (machine-readable)
  - `out/islamic_kids.txt` (human summary)

Optional: Write to Firestore (dev)
- Install Firestore client: `make install-ingest`
- Authenticate ADC: `gcloud auth application-default login`
- Set project: `export LUMENS_GCP_PROJECT=lumens-alnayeem-dev`
- Run ingest + Firestore write:
  - `make ingest-fs LIMIT=25`
  - or: `python -m services.ingest.cli --channels data/channels/islamic_kids.csv --out out/islamic_kids --limit 25 --firestore-project $LUMENS_GCP_PROJECT`

Next steps (suggested)
- Resolver: map each CSV `source_ref` to canonical `Channel.id = yt:{UCID}`; create `channels/*` and `communityChannels/*`.
- Ingest: fetch video metadata for each channel; write `content/*` with `provenance` and partial `signals`.
- Policy compile: validate YAML → JSON, store compiled snapshot in `policies/*` (and optionally GCS).
