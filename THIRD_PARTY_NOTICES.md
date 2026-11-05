# Third-Party Notices

`legends-jev` is licensed under the MIT License (`LICENSE`).

## Runtime Dependencies

- **Pillow** (`Pillow>=10.0.0`, installed via `pip`): Historical Permission Notice and Disclaimer (HPND) / MIT-CMU style license. Used locally for in-process JPEG/PNG image normalization into `280..1568` pixel bounds without spawning external shell processes. `Pillow` is not vendored inside this repository.

## Hosted Model Service

- **TypeSafe System One (`jev-1.14.0`)**: Accessed over HTTPS (`https://api.typesafe.ai/v1/`) only when `--execute` is explicitly supplied by the operator. No TypeSafe model weights or proprietary SDK code are bundled in this package.
