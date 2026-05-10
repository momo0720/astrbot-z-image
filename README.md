# astrbot-z-image

Generate images through a compatible text-to-image and image-edit API.

## Features

- Supports text-to-image and image-to-image generation.
- Supports asynchronous image edit polling and multi-key failover.

## Installation

1. Clone or download this repository.
2. Copy the `z_image` directory into your AstrBot plugin directory.
3. Open the AstrBot plugin configuration page and fill in the required settings.
4. Restart AstrBot or reload the plugin.

## Usage

- Main command: `/z画图`
- Detailed command examples: see `z_image/README.md`

## Repository Structure

- `z_image/main.py`
- `z_image/_conf_schema.json`
- `z_image/metadata.yaml`
- `z_image/README.md`

## Notes

- Sensitive local API endpoints and keys have been replaced with placeholders where applicable.
- Runtime-specific local config files are not included.
