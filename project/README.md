# Local screenshot collection

The 31 supplied PNGs are organized under the repository screenshots folder without changing image bytes or original
filenames. Every source matched the SHA256 in the existing
[evidence inventory](../infrastructure/portfolio-release/evidence-inventory.json).
Capture times remain unknown. This folder is an archive, not a second application.

| Local folder | Images | Contents |
| --- | ---: | --- |
| `../screenshots/dashboard-demo/` | 6 | Actual React captures with illustrative fixture values |
| `../screenshots/wso2-and-api/` | 5 | Approved API documentation and WSO2 configuration captures |
| `../screenshots/runtime-evidence/` | 2 | Approved sanitized SQL gateway events and alert evidence |
| `../screenshots/historical-reference/` | 7 | Historical or redundant captures; not selected for publication |
| `../screenshots/private-review/` | 11 | Previously excluded token, raw-address or personal-path captures |

**All local screenshot folders are ignored by Git**, including safe duplicates.
Private-review is an organizational label, not encryption or an access-control
boundary. Do not upload that folder or force-add its images. The token-bearing
capture remains sensitive even if the token has expired; review prior exposure
and credential rotation privately. No secrets were printed or rotated here.

Publish only the existing reviewed canonical copies in
[`../screenshots/final-blog/`](../screenshots/final-blog/). See the
[privacy audit](../docs/release-evidence-audit.md) for each image's provenance and
exclusion reason. Original filenames can be misleading: `04incidentdetails.png`
shows detection rules, and publication screens alone do not prove gateway routing.

[inventory.json](inventory.json) records the old-to-new relative paths, hashes,
categories and existing approved-copy locations. No screenshot was deleted,
generated, cropped, redacted or relabeled as a new runtime observation.
