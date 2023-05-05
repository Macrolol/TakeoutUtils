# LLM

# Google Activity Utility

A command-line utility to help you interact with your Google Drive and Google activity data.

## Features

1. Copy and extract a file from Google Drive to your local machine.
2. List your activities from the \`/My Activity/Search/MyActivity.html\` file with various output options such as format, information type, and number of entries to display.

## Prerequisites

- Python 3.6 or higher
- Install required packages by running: \`pip install -r requirements.txt\`

## Usage

```bash
python google_activity_utility.py [subcommand] --help for subcommand help
```

### Subcommands

#### 1. unzip-from-drive

Copy and extract a file from Google Drive to your local machine.

```bash
python google_activity_utility.py unzip-from-drive <source> <target>
\```

- `<source>`: Source path in Google Drive.
- `<target>`: Target path on the local machine.

#### 2. list-searches

List user activities from the `/My Activity/Search/MyActivity.html` file.

```bash
python google_activity_utility.py list-searches <path> --format=<format> --<info_option> [--<limit_option>=N]
```

- `<path>`: Path to \`MyActivity.html\` file.
- `--format`: Output format, either \`json\` or \`csv\`. Default is \`json\`.
- `<info_option>`: Choose one of the following mutually exclusive options:
  - `--all`: Output all activities.
  - `--searches_only`: Output searches only.
  - `--visited_only`: Output visited pages only.
- `<limit_option>`: Choose one of the following mutually exclusive options (optional):
  - `--head=N`: Output the latest N entries.
  - `--tail=N`: Output the oldest N entries.
  - `--every=N`: Output every N entries.

## Example

```bash
python google_activity_utility.py list-searches /path/to/MyActivity.html --format=json --all --head=10
```

This command will output the latest 10 activities in JSON format from the specified `MyActivity.html` file.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
